from qfluentwidgets import FluentIcon

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.key_setting_card import KeySettingCard
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from zzz_od.application.devtools.screenshot_helper.screenshot_helper_app import ScreenshotHelperApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.app_run_interface import AppRunInterface


class DevtoolsScreenshotHelperInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx

        top_widget = ColumnWidget()

        self.frequency_opt = TextSettingCard(icon=FluentIcon.GAME, title='截图间隔(秒)')
        self.frequency_opt.value_changed.connect(self._on_frequency_changed)
        top_widget.add_widget(self.frequency_opt)

        self.length_opt = TextSettingCard(icon=FluentIcon.GAME, title='持续时间(秒)')
        self.length_opt.value_changed.connect(self._on_length_changed)
        top_widget.add_widget(self.length_opt)

        self.key_save_opt = KeySettingCard(icon=FluentIcon.GAME, title='保存截图按键',
                                           content='按下后，保存 持续时间(秒) 内的截图')
        self.key_save_opt.value_changed.connect(self._on_key_save_changed)
        top_widget.add_widget(self.key_save_opt)

        self.dodge_detect_opt = SwitchSettingCard(icon=FluentIcon.GAME, title='闪避检测',
                                                  content='练习场中控制怪物无动作时，依然检测到需要闪避，截图保存用于优化模型')
        self.dodge_detect_opt.value_changed.connect(self._on_dodge_detect_changed)
        top_widget.add_widget(self.dodge_detect_opt)

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='devtools_screenshot_helper_interface',
            nav_text_cn='截图助手',
            parent=parent,
            widget_at_top=top_widget
        )

    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        AppRunInterface.on_interface_shown(self)
        self.frequency_opt.setValue(str(self.ctx.screenshot_helper_config.frequency_second))
        self.length_opt.setValue(str(self.ctx.screenshot_helper_config.length_second))
        self.key_save_opt.setValue(str(self.ctx.screenshot_helper_config.key_save))
        self.dodge_detect_opt.setValue(self.ctx.screenshot_helper_config.dodge_detect)

    def get_app(self) -> ZApplication:
        return ScreenshotHelperApp(self.ctx)

    def _on_frequency_changed(self, value: str) -> None:
        self.ctx.screenshot_helper_config.frequency_second = float(value)

    def _on_length_changed(self, value: str) -> None:
        self.ctx.screenshot_helper_config.length_second = float(value)

    def _on_key_save_changed(self, value: str) -> None:
        self.ctx.screenshot_helper_config.key_save = value

    def _on_dodge_detect_changed(self, value: bool) -> None:
        self.ctx.screenshot_helper_config.dodge_detect = value