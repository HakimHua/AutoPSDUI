import os
import sys
import zipfile
import unreal

from urllib.request import urlretrieve


def normal_dir(p_dir):
    return os.path.normpath(p_dir)


module_dir = normal_dir(os.path.dirname(__file__))

third_party_dir = normal_dir(os.path.join(module_dir, "../../../Source/ThirdParty/AutoPSDUI_Dependencies-1.0/"))

if sys.platform == "win32":
    third_party_dir = os.path.join(third_party_dir, "Win64")
    py_dir = os.path.join(
        unreal.Paths.engine_dir(), r"Engine\Binaries\ThirdParty\Python3\Win64"
    )
    py_exec = os.path.join(py_dir, "python.exe")
    pip_exec = os.path.join(py_dir, "Scripts/pip.exe")
elif sys.platform == "darwin":
    third_party_dir = os.path.join(third_party_dir, "Mac")
    py_dir = os.path.join(
        unreal.Paths.engine_dir(), r"Engine\Binaries\ThirdParty\Python3\Mac"
    )
    py_exec = os.path.join(py_dir, "python")
    pip_exec = os.path.join(py_dir, "Scripts/pip.exe")

sys.path.append(third_party_dir)

psd_gui_setting = unreal.AutoPSDUISetting.get()

third_party_url = "https://github.com/JohnSnowWind/AutoPSDUI_Dependencies/archive/refs/tags/v1.0.zip"


def download_dependencies():
    # slow task
    task_show = unreal.ScopedSlowTask(100, "Downloading Dependencies.")
    task_show.make_dialog(can_cancel=True)

    def progress(block_index, block_size, total_size):
        percent = int(100 * block_size * block_index / total_size)
        task_show.enter_progress_frame(percent, "Downloading Dependencies!")

    target_dir = os.path.join(third_party_dir, "..")
    target_file = os.path.join(target_dir, "third_party.zip")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    try:
        unreal.log("Start Downloading from %s" % third_party_url)
        urlretrieve(third_party_url,
                    target_file,
                    progress)
    except:
        message = "Download Failed: "
        unreal.log_error(message)
        unreal.EditorDialog.show_message(
            "ERROR", message, unreal.AppMsgType.OK, unreal.AppReturnType.OK
        )
        return False

    # Unzip
    zf_handle = zipfile.ZipFile(target_file)
    try:
        zf_handle.extractall(target_dir)
    except RuntimeError:
        message = "Unzip %s failed!" % target_file
        unreal.log_error(message)
        unreal.EditorDialog.show_message(
            "ERROR", message, unreal.AppMsgType.OK, unreal.AppReturnType.OK
        )
        return False

    return True
