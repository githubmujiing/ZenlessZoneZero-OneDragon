import os
import subprocess
import time
from typing import ClassVar, Optional


from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import WApplication
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanItem
from zzz_od.context.zzz_context import WContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.sola_guide.coagulation_field import CoagulationField
from zzz_od.operation.sola_guide.simulation_field import SimulationField
from zzz_od.operation.sola_guide.conquer_strong import ConquerStrong
from zzz_od.operation.sola_guide.silent_cleanup import SilentCleanup
from zzz_od.operation.sola_guide.tp_by_sola_guide import TransportBySolaGuide
from zzz_od.operation.control_okww_auto import start_okww_auto, kill_okww_auto
from zzz_od.operation.switch_teams import SwitchTeams


class ChargePlanApp(WApplication):

    STATUS_NO_PLAN: ClassVar[str] = '未配置体力计划'
    STATUS_ROUND_FINISHED: ClassVar[str] = '已完成一轮计划'

    def __init__(self, ctx: WContext):
        """
        体力计划
        """
        WApplication.__init__(
            self,
            ctx=ctx, app_id='charge_plan',
            op_name=gt('体力刷本', 'ui'),
            run_record=ctx.charge_plan_run_record
        )

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self.next_plan: Optional[ChargePlanItem] = None
        self.ctx.charge_plan_config.reset_plans()

    @operation_node(name='启动自动战斗', is_start_node=True)
    def start_auto(self) -> OperationRoundResult:
        start_okww_auto()
        return self.round_success()

    @node_from(from_name='模拟领域')
    @node_from(from_name='无音清剿')
    @node_from(from_name='讨伐强敌')
    @node_from(from_name='凝素领域')
    @node_from(from_name='启动自动战斗')
    @operation_node(name='换队与传送')
    def transport(self) -> OperationRoundResult:
        if not self.ctx.charge_plan_config.loop and self.ctx.charge_plan_config.all_plan_finished():
            return self.round_success(ChargePlanApp.STATUS_ROUND_FINISHED)

        next_plan = self.ctx.charge_plan_config.get_next_plan()
        if next_plan is None:
            return self.round_fail(ChargePlanApp.STATUS_NO_PLAN)

        self.next_plan = next_plan
        op= SwitchTeams(self.ctx, self.next_plan)
        op.execute()
        op = TransportBySolaGuide(self.ctx,
                                  next_plan.tab_name,
                                  next_plan.category_name,
                                  next_plan.mission_type_name)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='换队与传送')
    @operation_node(name='识别副本分类')
    def check_mission_type(self) -> OperationRoundResult:
        return self.round_success(self.next_plan.category_name)

    @node_from(from_name='识别副本分类', status='模拟领域')
    @operation_node(name='模拟领域')
    def simulation_field(self) -> OperationRoundResult:
        op = SimulationField(self.ctx, self.next_plan)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='识别副本分类', status='无音清剿')
    @operation_node(name='无音清剿')
    def silent_cleanup(self) -> OperationRoundResult:
        op = SilentCleanup(self.ctx, self.next_plan)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='识别副本分类', status='讨伐强敌')
    @operation_node(name='讨伐强敌')
    def conquer_strong(self) -> OperationRoundResult:
        op = ConquerStrong(self.ctx, self.next_plan)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='识别副本分类', status='凝素领域')
    @operation_node(name='凝素领域')
    def coagulation_field(self) -> OperationRoundResult:
        op = CoagulationField(self.ctx, self.next_plan)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='换队与传送', status=STATUS_ROUND_FINISHED)
    @node_from(from_name='模拟领域', status=SimulationField.STATUS_CHARGE_NOT_ENOUGH)
    @node_from(from_name='无音清剿', status=SilentCleanup.STATUS_CHARGE_NOT_ENOUGH)
    @node_from(from_name='讨伐强敌', status=ConquerStrong.STATUS_CHARGE_NOT_ENOUGH)
    @node_from(from_name='凝素领域', status=CoagulationField.STATUS_CHARGE_NOT_ENOUGH)
    @operation_node(name='返回大世界', is_start_node=True)
    def back_to_world(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='返回大世界')
    @operation_node(name='关闭自动战斗')
    def close_auto(self) -> OperationRoundResult:
        kill_okww_auto()
        time.sleep(2)
        return self.round_success()
