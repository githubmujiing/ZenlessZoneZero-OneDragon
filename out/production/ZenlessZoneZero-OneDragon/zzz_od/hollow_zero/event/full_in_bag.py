from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import WContext
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroSpecialEvent
from zzz_od.operation.zzz_operation import WOperation


class FullInBag(WOperation):

    def __init__(self, ctx: WContext):
        """
        确定出现事件后调用
        :param ctx:
        """
        WOperation.__init__(
            self, ctx,
            op_name=gt(HollowZeroSpecialEvent.FULL_IN_BAG.value.event_name)
        )

    @operation_node(name='丢弃', is_start_node=True)
    def drop(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_ocr_and_click(screen, '丢弃',
                                           success_wait=1, retry_wait=1)


def __debug():
    from zzz_od.context.zzz_context import WContext
    ctx = WContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    from one_dragon.utils import debug_utils
    screen = debug_utils.get_debug_image('bag_full')
    op = FullInBag(ctx)
    op.round_by_ocr_and_click(screen, '丢弃')


if __name__ == '__main__':
    __debug()