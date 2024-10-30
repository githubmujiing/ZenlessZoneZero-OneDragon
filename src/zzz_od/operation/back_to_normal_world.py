from cv2.typing import MatLike

from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import WContext
from zzz_od.game_data.agent import AgentEnum
# 尝试删除from zzz_od.hollow_zero.event import hollow_event_utils
# 尝试删除from zzz_od.hollow_zero.hollow_exit_by_menu import HollowExitByMenu
from zzz_od.operation.zzz_operation import WOperation


class BackToNormalWorld(WOperation):

    def __init__(self, ctx: WContext):
        """
        需要保证在任何情况下调用，都能返回大世界，让后续的应用可执行
        :param ctx:
        """
        WOperation.__init__(self, ctx, op_name=gt('返回大世界', 'ui'))

    def handle_init(self):
        pass

    @operation_node(name='画面识别', is_start_node=True, node_max_retry_times=60)
    def check_screen_and_run(self) -> OperationRoundResult:
        """
        识别游戏画面
        :return:
        """
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '大世界', '任务')

        if result.is_success:
            return self.round_success()


        # 这是领取完活每日奖励的情况
        area = self.ctx.screen_loader.get_area('索拉指南', '项目')
        result = self.round_by_ocr(screen, '活跃度', area=area)
        if result.is_success:
            self.round_by_click_area('菜单', '返回')
            return self.round_retry(wait=1)

        # 判断在副本大世界的情况
        result = self.round_by_find_area(screen, '副本大世界', '退出')
        if result.is_success:
            self.round_by_click_area('副本大世界', '退出', success_wait=2)
            screen = self.screenshot()
            area = self.ctx.screen_loader.get_area('副本大世界', '确认')
            self.round_by_ocr_and_click(screen, '确认', area=area)
            return self.round_retry(wait=1)

        # 判断在战斗画面


        # 这是在菜单的情况
        area = self.ctx.screen_loader.get_area('菜单', '中部列表')
        result = self.round_by_ocr(screen, '编队', area=area)
        if result.is_success:
            self.round_by_click_area('菜单', '返回')
            return self.round_retry(wait=1)

        click_back = self.round_by_click_area('菜单', '返回')
        if click_back.is_success:
            return self.round_retry(wait_round_time=1)
        else:
            return self.round_fail()


def __debug_op():
    ctx = WContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    op = BackToNormalWorld(ctx)
    ctx.start_running()
    op.execute()


if __name__ == '__main__':
    __debug_op()