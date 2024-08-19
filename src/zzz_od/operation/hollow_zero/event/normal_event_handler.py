from typing import List

from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.hollow_zero.game_data.hollow_zero_event import HallowZeroEvent
from zzz_od.operation.hollow_zero.event import event_utils
from zzz_od.operation.hollow_zero.event.event_ocr_result_handler import EventOcrResultHandler
from zzz_od.operation.zzz_operation import ZOperation


class NormalEventHandler(ZOperation):

    def __init__(self, ctx: ZContext, event: HallowZeroEvent):
        """
        确定出现事件后调用
        :param ctx:
        """
        event_name = event.event_name
        ZOperation.__init__(
            self, ctx,
            node_max_retry_times=5,
            op_name=gt(event_name)
        )

        self._handlers: List[EventOcrResultHandler] = []

        for opt in event.options:
            self._handlers.append(EventOcrResultHandler(
                target_cn=opt.ocr_word,
                status=opt.option_name,
                click_wait=opt.wait,
                lcs_percent=opt.lcs_percent
            ))
        self._handlers.append(
            EventOcrResultHandler(event_name, is_event_mark=True)
        )

    @operation_node(name='画面识别', is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        return event_utils.check_event_text_and_run(self, screen, self._handlers)


def __debug_opts():
    """
    识别图片输出选项
    :return:
    """
    from zzz_od.context.zzz_context import ZContext
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    from zzz_od.operation.hollow_zero.hollow_runner import HollowRunner
    op = HollowRunner(ctx)
    from one_dragon.utils import debug_utils
    screen = debug_utils.get_debug_image('_1724044474644')
    from zzz_od.operation.hollow_zero import hollow_utils
    event_name = hollow_utils.check_screen(op, screen)
    e = ctx.hollow.data_service.get_normal_event_by_name(event_name)
    op2 = NormalEventHandler(ctx, e)
    event_utils.check_event_text_and_run(op, screen, op2._handlers)


if __name__ == '__main__':
    __debug_opts()