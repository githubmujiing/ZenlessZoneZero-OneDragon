import time

from typing import Optional, ClassVar

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.config.charge_plan_config import ChargePlanItem
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class RoutineCleanup(ZOperation):

    STATUS_CHARGE_NOT_ENOUGH: ClassVar[str] = '电量不足'
    STATUS_CHARGE_ENOUGH: ClassVar[str] = '电量充足'

    def __init__(self, ctx: ZContext, plan: ChargePlanItem,
                 ):
        """
        使用快捷手册传送后
        用这个进行挑战
        :param ctx:
        """
        ZOperation.__init__(
            self, ctx,
            node_max_retry_times=5,
            op_name='%s %s' % (
                gt('定期清剿'),
                gt(plan.mission_type_name)
            )
        )

        self.plan: ChargePlanItem = plan

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self.charge_left: Optional[int] = None
        self.charge_need: Optional[int] = None

        self.auto_op: Optional[ConditionalOperator] = None

    @operation_node(name='等待入口加载', is_start_node=True)
    def wait_entry_load(self) -> OperationRoundResult:
        self.node_max_retry_times = 60  # 一开始等待加载要久一点
        screen = self.screenshot()
        return self.round_by_find_area(
            screen, '实战模拟室', '挑战等级',
            success_wait=1, retry_wait=1
        )

    # 传送过来已经是对的副本了
    # @node_from(from_name='等待入口加载')
    # @operation_node(name='选择副本')
    def choose_mission(self) -> OperationRoundResult:
        self.node_max_retry_times = 5

        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('定期清剿', '副本名称列表')
        part = cv2_utils.crop_image_only(screen, area.rect)

        target_point: Optional[Point] = None
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for ocr_result, mrl in ocr_result_map.items():
            if not str_utils.find_by_lcs(gt(self.plan.mission_type_name), ocr_result, percent=0.5):
                continue

            target_point = area.left_top + mrl.max + Point(0, 50)
            break

        if target_point is None:
            start = area.center
            end = start + Point(-100, 0)
            self.ctx.controller.drag_to(start=start, end=end)
            return self.round_retry(status='找不到 %s' % self.plan.mission_type_name, wait=1)

        click = self.ctx.controller.click(target_point)
        return self.round_success(wait=1)

    @node_from(from_name='等待入口加载')
    @operation_node(name='识别电量')
    def check_charge(self) -> OperationRoundResult:
        screen = self.screenshot()

        area = self.ctx.screen_loader.get_area('定期清剿', '剩余体力')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        self.charge_left = str_utils.get_positive_digits(ocr_result, None)
        if self.charge_left is None:
            return self.round_retry(status='识别 %s 失败' % '剩余体力', wait=1)

        area = self.ctx.screen_loader.get_area('定期清剿', '需要体力')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        self.charge_need = str_utils.get_positive_digits(ocr_result, None)
        if self.charge_need is None:
            return self.round_retry(status='识别 %s 失败' % '需要体力', wait=1)

        if self.charge_need > self.charge_left:
            return self.round_success(RoutineCleanup.STATUS_CHARGE_NOT_ENOUGH)

        self.can_run_times = self.charge_left // self.charge_need
        max_need_run_times = self.plan.plan_times - self.plan.run_times

        if self.can_run_times > max_need_run_times:
            self.can_run_times = max_need_run_times

        return self.round_success(RoutineCleanup.STATUS_CHARGE_ENOUGH)

    @node_from(from_name='识别电量', status=STATUS_CHARGE_ENOUGH)
    @operation_node(name='下一步')
    def click_next(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(
            screen, '实战模拟室', '下一步',
            success_wait=1, retry_wait_round=1
        )

    @node_from(from_name='下一步')
    @operation_node(name='出战')
    def click_start(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(
            screen, '实战模拟室', '出战',
            success_wait=1, retry_wait_round=1
        )

    @node_from(from_name='出战')
    @node_from(from_name='判断下一次', status='战斗结果-再来一次')
    @operation_node(name='自动战斗初始化')
    def init_auto_battle(self) -> OperationRoundResult:
        if self.auto_op is not None:  # 如果有上一个 先销毁
            self.auto_op.dispose()
        self.auto_op = AutoBattleOperator(self.ctx, 'auto_battle', self.plan.auto_battle_config)
        if not self.auto_op.is_file_exists():
            return self.round_fail('无效的自动战斗指令 请重新选择')
        self.auto_op.init_operator()

        self.ctx.yolo.init_context(True)
        self.ctx.battle.init_context()

        return self.round_success()

    @node_from(from_name='自动战斗初始化')
    @operation_node(name='等待战斗画面加载')
    def wait_battle_screen(self) -> OperationRoundResult:
        self.node_max_retry_times = 60  # 战斗加载的等待时间较长
        screen = self.screenshot()
        result = self.round_by_find_area(screen, '战斗画面', '按钮-普通攻击', retry_wait_round=1)
        if result.is_success:
            self.auto_op.start_running_async()
        return result

    @node_from(from_name='等待战斗画面加载')
    @operation_node(name='自动战斗')
    def auto_battle(self) -> OperationRoundResult:
        if self.ctx.battle.is_battle_end():
            self.auto_op.stop_running()
            return self.round_success()
        now = time.time()
        screen = self.screenshot()

        self.ctx.yolo.check_screen(screen, now)
        self.ctx.battle.check_screen(screen, now, self.auto_op.get('allow_ultimate', None))

        return self.round_wait(wait=self.ctx.battle_assistant_config.screenshot_interval)

    @node_from(from_name='自动战斗')
    @operation_node(name='战斗结束')
    def after_battle(self) -> OperationRoundResult:
        self.node_max_retry_times = 5  # 战斗结束恢复重试次数
        # TODO 还没有判断战斗失败
        self.can_run_times -= 1
        self.ctx.charge_plan_config.add_plan_run_times(self.plan)
        return self.round_success()

    @node_from(from_name='战斗结束')
    @operation_node(name='判断下一次')
    def check_next(self) -> OperationRoundResult:
        screen = self.screenshot()
        if self.can_run_times == 0:
            return self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-完成',
                                                     success_wait=5, retry_wait_round=1)
        else:
            return self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-再来一次',
                                                     success_wait=1, retry_wait_round=1)

def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()
    op = RoutineCleanup(ctx, ChargePlanItem(
        category_name='定期清剿',
        mission_type_name='怪兽与怪客'
    ))
    op.execute()


if __name__ == '__main__':
    __debug()
