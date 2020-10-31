#!/bin/env python3

"""Welcome screen application for EasyArch.

This script uses Gtk 3 (PyGObject) to allow user setup his desktop layout and
theme and provides a few useful links to some important websites.

Copyright (C) 2020 Asif Mahmud Shimon

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA 02111-1307 USA
"""

import os
import subprocess
import abc
import re
import sys

from typing import (
    Iterable,
    List,
    Dict,
    Callable,
)

try:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk, GdkPixbuf, cairo
except Exception as ex:
    raise ex


"""
Global variables
"""
DEFAULT_THEME = "Materia-compact"
CURRENT_THEME = ""
STACK: Gtk.Stack = None
BUILDER: Gtk.Builder = None
LAYOUT_PAGE_NAME: str = "layout_page"
THEME_PAGE_NAME: str = "theme_page"
WELCOME_PAGE_NAME: str = "welcome_page"
HEADERBAR: str = "headerbar"
LEFT_NAV_BTN: str = "left_nav_btn"
RIGHT_NAV_BTN: str = "right_nav_btn"
WINDOW_ICON_NAME: str = "images/icon.png"

LAYOUT_BH_BTN: str = "layout_bh_btn"
LAYOUT_TH_BTN: str = "layout_th_btn"
LAYOUT_LV_BTN: str = "layout_lv_btn"
LAYOUT_RV_BTN: str = "layout_rv_btn"
LAYOUT_IMAGE_NAMES: Dict[str, str] = {
    LAYOUT_BH_BTN: "images/layout-bh.png",
    LAYOUT_TH_BTN: "images/layout-th.png",
    LAYOUT_LV_BTN: "images/layout-lv.png",
    LAYOUT_RV_BTN: "images/layout-rv.png",
}
LAYOUT_PIXBUFS: Dict[str, GdkPixbuf.Pixbuf] = {
    LAYOUT_BH_BTN: None,
    LAYOUT_TH_BTN: None,
    LAYOUT_LV_BTN: None,
    LAYOUT_RV_BTN: None,
}

THEME_DARK_CHECKBOX: str = "prefer_dark_theme_check"

ARCHLINUX_LOGO_IMG: str = "archlinux_logo_img"
ARCHLINUX_LOGO_IMG_NAME: str = "images/archlinux-logo.png"
WELCOME_LABEL: str = "welcome_label"
WELCOME_LABEL_TEXT: str = "Welcome to Archlinux"
WELCOME_SUBLABEL: str = "welcome_sublabel"
WELCOME_SUBLABEL_TEXT: str = """
Enjoy the power of simplicity and a
vast collection of up-to-date software.
"""


class BaseCommand(abc.ABC):
    """Represents a single command.

    Command can be shell command or python function to be executed depending on
    the implementation. Either way the `execute` method will actually run the
    command.
    """

    def __init__(self, check: bool = True):
        """
        @brief      Create a command representitive.

        @param      check  Whether or not to check the return value

        @return     None
        """
        self.__check = check

    @abc.abstractmethod
    def execute(self) -> str:
        """
        @brief      Child classes must implement this method.

        @details    It is up to the child implementation to modify the
        arguments as it needs. Thats why this method exists. After
        creating the list of args child can call _run method to
        actually execute the command and return the result.

        @param      None

        @return     List of strings. Output of the command execution.
        """
        pass

    def _run(self, args: List[str]) -> List[str]:
        """
        @brief      Execute the command represented by args.

        @details    Upon execution return value will be checke. Finally the
        outputs will be parsed and a list of strings will be constructed with
        them. Empty lines will be omitted and all the lines will be
        stripped. This may raise exception if the command is not found.

        @param      args List[str]

        @return     List of strings
        """
        res: subprocess.CompletedProcess = subprocess.run(
            args,
            check=self.__check,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if res.returncode != 0:
            return []

        res_str: str = res.stdout.decode("utf8")
        res_str_list: List[str] = res_str.split("\n")
        ret_str_list = list()
        for rs in res_str_list:
            rs = rs.strip()
            if rs:
                ret_str_list.append(rs)
        return ret_str_list


class XfceCommand(BaseCommand):
    """Represents a single `xfconf-query` command."""

    def __init__(
        self,
        *args: Iterable[str],
        exe: str = "xfconf-query",
        **kw,
    ):
        """
        @brief      Initialize command object.

        @param      args   List of strings to be send to the command
        @param      exe    Executable path
        """
        super().__init__(**kw)
        self.__exe = exe
        self.__args = args

    def execute(self) -> List[str]:
        """
        @brief      Run the command and return its output.

        @details    This can raise `CalledProcessError` in case the command
        return value was non zero. Output of both stdout and stderr will be
        captured and formatted into utf8 string list. Every string in the
        output will be stripped off of whitespaces from both ends.

        @param      None

        @return     List of string
        """
        args = [
            self.__exe,
        ]
        args.extend(self.__args)
        ret_str_list = self._run(args)
        return ret_str_list


class ShellCommand(BaseCommand):
    """Represents a shell command."""

    def __init__(self, *args, **kw):
        """
        @brief      Construct a generic shell command.

        @details    Allows user to run a shell command using an instance of
        this class.

        @param      args     List of arguments as string.

        @param      kw       Keyword arguments passed to the parent.

        @return     None
        """
        super().__init__(**kw)
        self.__args = args

    def execute(self) -> List[str]:
        """
        @brief      Run the command.

        @param      None

        @return     List of strings
        """
        return self._run(self.__args)


class Qt5IconChangeCommand(BaseCommand):
    """Represents an operation to replace the icon theme in qt5ct conf."""

    def __init__(self, theme: str):
        self.__theme = theme

    def execute(self):
        conf_path: str = os.path.expanduser("~/.config/qt5ct/qt5ct.conf")
        with open(conf_path, "r") as f:
            data = f.read()

        new_data = re.sub(
            "icon_theme=(.*)",
            f"icon_theme={self.__theme}",
            data,
        )

        with open(conf_path, "w") as f:
            f.write(new_data)


def get_cur_theme() -> str:
    """
    @brief      Get the current theme name

    @details    This can throw exception in case of failure.

    @param      None

    @return     str
    """
    cur_theme_cmd = XfceCommand(
        "-c",
        "xsettings",
        "-p",
        "/Net/ThemeName",
    )
    res = cur_theme_cmd.execute()
    if not res:
        raise RuntimeError("Could not determine current theme.")

    return res[0]


def get_panel_number() -> int:
    """
    @brief      Get the panel id.

    @param      None

    @return     int
    """
    command = XfceCommand("-c", "xfce4-panel", "-p", "/panels")
    res = command.execute()
    panel_id = 0
    try:
        tmp = int(res[-1])
        panel_id = tmp
    except Exception:
        pass
    return panel_id


def resolve_path(fileName: str) -> str:
    """
    @brief      Resolve a file path

    @details This tries to find the file under some specific folders. These
    folders include the script folder, `/usr/share/easyarch-welcome/`,
    `/etc/easyarch-welcome` in the same sequence. First existing path will be
    returned. If no path could be resolved then `None` is returned.

    @param      fileName   string file name(i.e layout-bh.png)

    @return     str or None
    """
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    path_list = [
        cur_dir,
        "/usr/share/easyarch-welcome",
        "/etc/easyarch-welcome",
    ]
    for path in path_list:
        full_path = os.path.join(path, fileName)
        if os.path.exists(full_path):
            return full_path
    return None


def check_virtual_machine() -> bool:
    """
    @brief      Check whether we are running a VM or not.

    @details    Uses systemd to detect virtualization.

    @param      None

    @return     bool
    """
    prog = subprocess.run(
        [
            "systemd-detect-virt",
        ],
        capture_output=True,
        universal_newlines=True,
    )
    if prog.returncode != 0 or prog.stdout == "none":
        return False
    return True


def get_xresolution():
    """
    @brief      Return supported display resolutions.

    @details    This runs the xrandr program to collect and return the
    supported display resolutions.

    @param      None

    @return     List of strings
    """
    data = ""
    prog = subprocess.run(
        [
            "xrandr",
        ],
        capture_output=True,
        universal_newlines=True,
    )
    if prog.returncode != 0:
        exit(-1)
    data = prog.stdout
    data = data.split("\n")
    expr = re.compile(r"\s+(\d+x\d+)\s+")
    rv = list()
    for line in data:
        resMatch = re.search(expr, line)
        if resMatch:
            rv.append(resMatch[0].strip())
    return rv


def apply_resolution(widget: Gtk.ComboBoxText):
    """
    @brief      Apply selected resolution from the combobox.

    @param      widget     Gtk.ComboBoxText

    @return     None
    """
    # apply resolution for all displays in the xfce settings
    res_str = widget.get_active_text()
    cmd = XfceCommand("-c", "displays", "-p", "/ActiveProfile")
    cmd_res = cmd.execute()

    print("Walking through active display profiles")
    for cr in cmd_res:
        print(f"Profile: {cr}")
        cmd_2 = XfceCommand("-c", "displays", "-p", f"/{cr}", "-l")
        cmd_res_2 = cmd_2.execute()

        print("Walking through profile keys")
        for cr2 in cmd_res_2:
            if "Resolution" in cr2:
                print(f"Found resolution in {cr2}")
                cmd_3 = XfceCommand(
                    "-c",
                    "displays",
                    "-p",
                    cr2,
                    "-s",
                    res_str,
                )
                cmd_3.execute()

    # also use xrandr to change current resolution
    xrandr_cmd = ShellCommand("xrandr", "-s", res_str)
    xrandr_cmd.execute()


def init_res_app() -> Gtk.ApplicationWindow:
    """
    @brief      Initialize the resolution settings app.

    @details    Initialize and return the xrandr resolution settings
    application.

    @param      None

    @return     Gtk.ApplicationWindow
    """
    window: Gtk.ApplicationWindow = Gtk.ApplicationWindow()

    vbox: Gtk.VBox = Gtk.VBox()
    vbox.props.border_width = 10
    vbox.props.spacing = 20

    label: Gtk.Label = Gtk.Label()
    label.set_markup(
        "<big>Seems like you are running a virtual machine."
        + "Would you like to switch display resolution ?</big>"
    )
    label.set_justify(Gtk.Justification.CENTER)
    label.props.wrap = True
    # vbox.add(label)
    vbox.pack_start(label, False, False, 0)

    hbox: Gtk.HBox = Gtk.HBox()
    hbox.props.spacing = 20
    # vbox.add(hbox)
    vbox.pack_start(hbox, False, False, 0)

    label2: Gtk.Label = Gtk.Label()
    label2.set_markup("<big>Select Resolution</big>")
    label2.set_justify(Gtk.Justification.RIGHT)
    hbox.pack_start(label2, False, False, 0)

    resolutions = get_xresolution()
    combobox: Gtk.ComboBoxText = Gtk.ComboBoxText()
    for res in resolutions:
        combobox.append_text(res)
    combobox.set_entry_text_column(0)
    if len(resolutions) > 0:
        combobox.set_active(0)
    # combobox.connect(
    #     "changed",
    #     lambda w: print(w.get_active_text()),
    # )
    hbox.add(combobox)

    hbox2: Gtk.HBox = Gtk.HBox()
    hbox2.props.spacing = 10
    # vbox.add(hbox2)
    vbox.pack_end(hbox2, False, False, 0)

    apply_btn: Gtk.Button = Gtk.Button(label="Apply")
    apply_icon: Gtk.Image = Gtk.Image.new_from_icon_name(
        "dialog-ok",
        Gtk.IconSize.BUTTON,
    )
    apply_btn.set_image(apply_icon)
    apply_btn.connect(
        "clicked",
        lambda w: apply_resolution(combobox),
    )
    hbox2.add(apply_btn)

    exit_btn: Gtk.Button = Gtk.Button(label="Exit")
    exit_icon: Gtk.Image = Gtk.Image.new_from_icon_name(
        "window-close",
        Gtk.IconSize.BUTTON,
    )
    exit_btn.set_image(exit_icon)
    exit_btn.connect(
        "clicked",
        lambda w: window.close(),
    )
    hbox2.add(exit_btn)

    headerbar: Gtk.HeaderBar = Gtk.HeaderBar()
    headerbar.props.show_close_button = True
    headerbar.set_title("Set Resolution")
    window.set_titlebar(headerbar)

    window_icon: GdkPixbuf.Pixbuf = GdkPixbuf.Pixbuf.new_from_file(
        resolve_path("images/icon.png"),
    )

    window.add(vbox)
    window.props.default_width = 400
    window.set_title("Set Resolution")
    window.set_icon(window_icon)

    return window


def load_pixbufs():
    """
    @brief      Preload some pixel buffers into memory.

    @details    Some images are needed to pre-load before the app starts. This
    is where that operation takes place. For example the layout button images
    are loaded in this function. As consequence this function should be called
    before setting up the app or the ui itself.

    @param      None

    @return     None
    """
    global LAYOUT_PIXBUFS
    for layout in LAYOUT_IMAGE_NAMES:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            resolve_path(LAYOUT_IMAGE_NAMES[layout])
        )
        LAYOUT_PIXBUFS[layout] = pixbuf


"""
Layout configurations along with setup commands.
"""
PANEL_ID = get_panel_number()
LAYOUT_COMMANDS: Dict[str, List[BaseCommand]] = {
    "bottom_horizontal": [
        XfceCommand(
            "-c",
            "xfce4-panel",
            "-p",
            f"/panels/panel-{PANEL_ID}/position",
            "-s",
            "p=8;x=0;y=0",
        ),
        XfceCommand(
            "-c",
            "xfce4-panel",
            "-p",
            f"/panels/panel-{PANEL_ID}/mode",
            "-s",
            "0",
        ),
    ],
    "top_horizontal": [
        XfceCommand(
            "-c",
            "xfce4-panel",
            "-p",
            f"/panels/panel-{PANEL_ID}/position",
            "-s",
            "p=6;x=0;y=0",
        ),
        XfceCommand(
            "-c",
            "xfce4-panel",
            "-p",
            f"/panels/panel-{PANEL_ID}/mode",
            "-s",
            "0",
        ),
    ],
    "left_vertical": [
        XfceCommand(
            "-c",
            "xfce4-panel",
            "-p",
            f"/panels/panel-{PANEL_ID}/position",
            "-s",
            "p=6;x=0;y=0",
        ),
        XfceCommand(
            "-c",
            "xfce4-panel",
            "-p",
            f"/panels/panel-{PANEL_ID}/mode",
            "-s",
            "1",
        ),
    ],
    "right_vertical": [
        XfceCommand(
            "-c",
            "xfce4-panel",
            "-p",
            f"/panels/panel-{PANEL_ID}/position",
            "-s",
            "p=2;x=0;y=0",
        ),
        XfceCommand(
            "-c",
            "xfce4-panel",
            "-p",
            f"/panels/panel-{PANEL_ID}/mode",
            "-s",
            "1",
        ),
    ],
}


"""
Theme configurations along with variants and setup commands.
"""
THEME_COLLECTION: Dict[str, Dict[str, BaseCommand]] = {
    "default_theme": {
        "light": [
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Materia-compact"
            ),
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "Adwaita++"
            ),
            XfceCommand("-c", "xfwm4", "-p", "/general/theme", "-s", "Materia-compact"),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "36"),
            Qt5IconChangeCommand("Adwaita++"),
        ],
        "dark": [
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Materia-dark-compact"
            ),
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "Adwaita++-Dark"
            ),
            XfceCommand(
                "-c", "xfwm4", "-p", "/general/theme", "-s", "Materia-dark-compact"
            ),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "36"),
            Qt5IconChangeCommand("Adwaita++-Dark"),
        ],
    },
    "win10_theme": {
        "light": [
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Windows-10-3.2"
            ),
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "Windows-10-1.0"
            ),
            XfceCommand("-c", "xfwm4", "-p", "/general/theme", "-s", "Win10-Light"),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "36"),
            Qt5IconChangeCommand("Windows-10-1.0"),
        ],
        "dark": [
            XfceCommand(
                "-c",
                "xsettings",
                "-p",
                "/Net/ThemeName",
                "-s",
                "Windows-10-Dark-3.2-dark",
            ),
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "Windows-10-1.0"
            ),
            XfceCommand("-c", "xfwm4", "-p", "/general/theme", "-s", "Win10-Dark"),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "36"),
            Qt5IconChangeCommand("Windows-10-1.0"),
        ],
    },
    "win7_theme": {
        "default": [
            XfceCommand("-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Windows-7"),
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "Windows-7"
            ),
            XfceCommand("-c", "xfwm4", "-p", "/general/theme", "-s", "X-Aero GTK3"),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "36"),
            Qt5IconChangeCommand("Windows-7"),
        ],
    },
    "winxp_theme": {
        "default": [
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Windows XP Luna"
            ),
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "Windows-XP"
            ),
            XfceCommand("-c", "xfwm4", "-p", "/general/theme", "-s", "Windows XP Luna"),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "36"),
            Qt5IconChangeCommand("Windows-XP"),
        ],
    },
    "win95_theme": {
        "default": [
            XfceCommand("-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Chicago95"),
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "Chicago95"
            ),
            XfceCommand("-c", "xfwm4", "-p", "/general/theme", "-s", "Chicago95"),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "44"),
            Qt5IconChangeCommand("Chicago95"),
        ],
    },
    "mac_theme": {
        "light": [
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Sierra-light"
            ),
            XfceCommand(
                "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", "McMojave-circle"
            ),
            XfceCommand("-c", "xfwm4", "-p", "/general/theme", "-s", "Sierra-light"),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "36"),
            Qt5IconChangeCommand("McMojave-circle"),
        ],
        "dark": [
            XfceCommand("-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Sierra-dark"),
            XfceCommand(
                "-c",
                "xsettings",
                "-p",
                "/Net/IconThemeName",
                "-s",
                "McMojave-circle-dark",
            ),
            XfceCommand("-c", "xfwm4", "-p", "/general/theme", "-s", "Sierra-dark"),
            XfceCommand("-c", "xfce4-panel", "-p", "/panels/panel-1/size", "-s", "36"),
            Qt5IconChangeCommand("McMojave-circle-dark"),
        ],
    },
}


def on_window_destroy(window: Gtk.Widget, *args):
    """
    @brief      Window close event handler.

    @details    Before closing the application it will look for autostart
    file, if found will delete it so that on next login, the app won't
    automatically start.

    @param      window   Gtk.Widget

    @param      args     place holder list

    @return     None
    """
    print("exiting main app")
    auto_start_path: str = os.path.expanduser(
        "~/.config/autostart/welcome-screen.desktop",
    )
    if os.path.exists(auto_start_path):
        print("autostart file exists, removing")
        os.remove(auto_start_path)

    Gtk.main_quit()


def on_left_nav_btn_clicked(btn: Gtk.Widget, *args):
    """
    @brief      Handle previous page navigation.

    @details    This function will be called when the `Prev` button is
    available and clicked from the ui.

    @param      btn      Gtk.Widget

    @param      args     place holder list

    @return     None
    """
    name: str = STACK.get_visible_child_name()
    if name == THEME_PAGE_NAME:
        STACK.set_visible_child_name(LAYOUT_PAGE_NAME)
    elif name == WELCOME_PAGE_NAME:
        STACK.set_visible_child_name(THEME_PAGE_NAME)


def on_right_nav_btn_clicked(btn: Gtk.Widget, *args):
    """
    @brief      Handles next page navigation click.

    @details    This function is called when the `Next` button is
    available and clicked from the ui.

    @param      btn      Gtk.Widget

    @param      args     place holder list

    @return     None
    """
    name: str = STACK.get_visible_child_name()
    if name == LAYOUT_PAGE_NAME:
        STACK.set_visible_child_name(THEME_PAGE_NAME)
    elif name == THEME_PAGE_NAME:
        STACK.set_visible_child_name(WELCOME_PAGE_NAME)


def on_page_map(page: Gtk.Widget, *args):
    """
    @brief      Updates the visuals of headerbar on page change.

    @details    This function is called whenever a page in the `stack`
    is mapped/displayed. So we get a chance to change the state of
    the navigation buttions and the title of the headerbar.

    @param      page     Gtk.Widget

    @param      args     place holder list

    @return     None
    """
    # print("Page map called")
    name: str = STACK.get_visible_child_name()
    headerbar: Gtk.HeaderBar = BUILDER.get_object(HEADERBAR)
    left_nav_btn: Gtk.Button = BUILDER.get_object(LEFT_NAV_BTN)
    right_nav_btn: Gtk.Button = BUILDER.get_object(RIGHT_NAV_BTN)
    if name == LAYOUT_PAGE_NAME:
        left_nav_btn.set_visible(False)
        right_nav_btn.set_visible(True)
        headerbar.props.title = "Select desktop layout"
    elif name == THEME_PAGE_NAME:
        left_nav_btn.set_visible(True)
        right_nav_btn.set_visible(True)
        headerbar.props.title = "Select desktop theme"
    else:
        left_nav_btn.set_visible(True)
        right_nav_btn.set_visible(False)
        headerbar.props.title = "Enjoy Archlinux"


def on_layout_bh_btn_img_draw(
    image: Gtk.DrawingArea,
    context: cairo.Context,
    *args,
):
    """
    @brief      Updates the image size along with the change of button size.

    @details    Whenever the corresponding layout button is resized this
    function is called to allow us resize and redraw the buttion's image.

    @param      image    Gtk.DrawingArea

    @param      context  Cairo drawing context associated with the button

    @param      args     place holder list

    @return     None
    """
    size, _ = image.get_allocated_size()
    width: int = size.width
    height: int = size.height
    # print(f"w={width}, h={height}")
    scaled_pixbuf = LAYOUT_PIXBUFS[LAYOUT_BH_BTN].scale_simple(
        width,
        height,
        GdkPixbuf.InterpType.BILINEAR,
    )
    Gdk.cairo_set_source_pixbuf(context, scaled_pixbuf, 0, 0)
    context.paint()


def on_layout_th_btn_img_draw(
    image: Gtk.DrawingArea,
    context: cairo.Context,
    *args,
):
    """
    @brief      Updates the image size along with the change of button size.

    @details    Whenever the corresponding layout button is resized this
    function is called to allow us resize and redraw the buttion's image.

    @param      image    Gtk.DrawingArea

    @param      context  Cairo drawing context associated with the button

    @param      args     place holder list

    @return     None
    """
    size, _ = image.get_allocated_size()
    width: int = size.width
    height: int = size.height
    # print(f"w={width}, h={height}")
    scaled_pixbuf = LAYOUT_PIXBUFS[LAYOUT_TH_BTN].scale_simple(
        width,
        height,
        GdkPixbuf.InterpType.BILINEAR,
    )
    Gdk.cairo_set_source_pixbuf(context, scaled_pixbuf, 0, 0)
    context.paint()


def on_layout_lv_btn_img_draw(
    image: Gtk.DrawingArea,
    context: cairo.Context,
    *args,
):
    """
    @brief      Updates the image size along with the change of button size.

    @details    Whenever the corresponding layout button is resized this
    function is called to allow us resize and redraw the buttion's image.

    @param      image    Gtk.DrawingArea

    @param      context  Cairo drawing context associated with the button

    @param      args     place holder list

    @return     None
    """
    size, _ = image.get_allocated_size()
    width: int = size.width
    height: int = size.height
    # print(f"w={width}, h={height}")
    scaled_pixbuf = LAYOUT_PIXBUFS[LAYOUT_LV_BTN].scale_simple(
        width,
        height,
        GdkPixbuf.InterpType.BILINEAR,
    )
    Gdk.cairo_set_source_pixbuf(context, scaled_pixbuf, 0, 0)
    context.paint()


def on_layout_rv_btn_img_draw(
    image: Gtk.DrawingArea,
    context: cairo.Context,
    *args,
):
    """
    @brief      Updates the image size along with the change of button size.

    @details    Whenever the corresponding layout button is resized this
    function is called to allow us resize and redraw the buttion's image.

    @param      image    Gtk.DrawingArea

    @param      context  Cairo drawing context associated with the button

    @param      args     place holder list

    @return     None
    """
    size, _ = image.get_allocated_size()
    width: int = size.width
    height: int = size.height
    # print(f"w={width}, h={height}")
    scaled_pixbuf = LAYOUT_PIXBUFS[LAYOUT_RV_BTN].scale_simple(
        width,
        height,
        GdkPixbuf.InterpType.BILINEAR,
    )
    Gdk.cairo_set_source_pixbuf(context, scaled_pixbuf, 0, 0)
    context.paint()


def on_layout_btn_clicked(button: Gtk.Button, *args):
    """
    @brief      Change desktop layout on layout button click.

    @details    In the layout regarding button must be named
    after the target layout name int LAYOUT_COMMANDS dictionary.

    @param      button   Gtk.Button button widget that recieved
    clicked event.

    @param      args     place holder list

    @return     None
    """
    name: str = button.get_name()
    print("Layout Name: ", name)
    commands = LAYOUT_COMMANDS[name]
    for cmd in commands:
        cmd.execute()


def apply_theme(theme: str = None, dark: bool = False):
    """
    @brief      Function to apply a global theme.

    @details    This function tries to determine which theme to
    apply and which variant to apply. If the variant is available
    then applies that variant else applies the default theme of
    that name.

    @param      theme     str   theme name

    @param      dark      bool  theme variant flag

    @return     None
    """
    if not theme:
        for theme_name in THEME_COLLECTION:
            widget_id = f"{theme_name}_choice"
            widget: Gtk.RadioButton = BUILDER.get_object(widget_id)
            selected: bool = widget.get_active()
            if selected:
                theme = theme_name
                break
    print(f"Theme: {theme}, Dark: {dark}")
    if theme not in THEME_COLLECTION:
        print("Theme not found")
        return

    theme_dict: Dict[str, List[BaseCommand]] = THEME_COLLECTION[theme]
    theme_commands: List[BaseCommand] = None
    if dark:
        if "dark" in theme_dict:
            print("Dark variant is selected")
            theme_commands = theme_dict["dark"]
        else:
            print("Default variant is selected")
            theme_commands = theme_dict["default"]
    else:
        if "light" in theme_dict:
            print("Light variant is selected")
            theme_commands = theme_dict["light"]
        else:
            print("Default variant is selected")
            theme_commands = theme_dict["default"]

    for cmd in theme_commands:
        cmd.execute()


def on_prefer_dark_theme_check_toggled(check: Gtk.CheckButton, *args):
    """
    @brief      Handler for theme variant checkbox.

    @details    This is called when the theme variant checkbox is toggled.

    @param      check    Gtk.CheckButton

    @param      args     place holder list

    @return     None
    """
    status = check.get_active()
    # print(f"Toggle status: {status}")
    apply_theme(dark=status)


def on_theme_choice_changed(choice: Gtk.RadioButton, *args):
    """
    @brief      Handler for theme choice change.

    @details    This is called when status of any theme choice radio button is
    changed.

    @param      choice   Gtk.RadioButton

    @param      args     place holder list

    @return     None
    """
    name: str = choice.get_name()
    selected: bool = choice.get_active()
    if selected:
        # print(f"Selected theme: {name}")
        dark_checkbox: Gtk.CheckButton = BUILDER.get_object(
            THEME_DARK_CHECKBOX,
        )
        dark_mode: bool = dark_checkbox.get_active()
        apply_theme(theme=name, dark=dark_mode)


"""
Dictionary of all GUI handlers.
"""
HANDLERS: Dict[str, Callable] = {
    "on_window_destroy": on_window_destroy,
    "on_page_map": on_page_map,
    "on_left_nav_btn_clicked": on_left_nav_btn_clicked,
    "on_right_nav_btn_clicked": on_right_nav_btn_clicked,
    "on_layout_bh_btn_img_draw": on_layout_bh_btn_img_draw,
    "on_layout_th_btn_img_draw": on_layout_th_btn_img_draw,
    "on_layout_lv_btn_img_draw": on_layout_lv_btn_img_draw,
    "on_layout_rv_btn_img_draw": on_layout_rv_btn_img_draw,
    "on_layout_btn_clicked": on_layout_btn_clicked,
    "on_prefer_dark_theme_check_toggled": on_prefer_dark_theme_check_toggled,
    "on_theme_choice_changed": on_theme_choice_changed,
}


def show_welcome_app(*args):
    """
    @brief      Show the welcome application.

    @details    This application should provide with a simple ui to allow user
    to setup the desktop layout, theme and othere stuffs.

    @param      args   Just placeholder

    @return     None
    """
    global STACK, BUILDER

    load_pixbufs()

    BUILDER = Gtk.Builder()
    BUILDER.add_from_file(resolve_path("ui/WelcomeApp.glade"))

    STACK = BUILDER.get_object("stack")

    # set archlinux logo image in welcome page
    archlogo_pixbuf: GdkPixbuf.Pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
        resolve_path(ARCHLINUX_LOGO_IMG_NAME),
        180,
        -1,
        True,
    )
    archlogo_img: Gtk.Image = BUILDER.get_object(ARCHLINUX_LOGO_IMG)
    archlogo_img.set_from_pixbuf(archlogo_pixbuf)

    # set welcome page texts
    welcome_label: Gtk.Label = BUILDER.get_object(WELCOME_LABEL)
    welcome_label.set_label(WELCOME_LABEL_TEXT)
    welcome_sublabel: Gtk.Label = BUILDER.get_object(WELCOME_SUBLABEL)
    welcome_sublabel.set_label(WELCOME_SUBLABEL_TEXT)

    # set window icon
    window: Gtk.ApplicationWindow = BUILDER.get_object("window")
    window.set_icon(
        GdkPixbuf.Pixbuf.new_from_file(
            resolve_path(WINDOW_ICON_NAME),
        ),
    )

    BUILDER.connect_signals(HANDLERS)

    window.show_all()


def main():
    """
    @brief      Main loop for the GUI.

    @param      None

    @return     None
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("running in test mode")
        res_app = init_res_app()
        res_app.connect(
            "destroy",
            show_welcome_app,
        )
        res_app.show_all()
    else:
        is_first_run = True
        if os.path.exists(
            os.path.expanduser(
                "~/.config/welcome_screen",
            )
        ):
            is_first_run = False
        is_vm = check_virtual_machine()

        if is_first_run:
            print("first time run, creating indicator file")
            with open(
                os.path.expanduser(
                    "~/.config/welcome_screen",
                ),
                "w",
            ) as f:
                f.write("1\n")
        if is_first_run and is_vm:
            print("running res app first")
            res_app = init_res_app()
            res_app.connect(
                "destroy",
                show_welcome_app,
            )
            res_app.show_all()
        else:
            print("running main app directly")
            show_welcome_app()
    Gtk.main()


if __name__ == "__main__":
    main()
