import os
import sys
import getopt
from importlib import reload

import unreal

dst_path = "/Game"

default_font = unreal.AutoPSDUISetting.get().default_font
font_map = unreal.AutoPSDUISetting.get().font_map


# Check Whether psd_tools has been installed
def check_psd_tools():
    psd_tools_exists = False
    try:
        import psd_tools
        return True
    except ModuleNotFoundError:
        # Check To Install psd_tools
        # Use Custom Site or Default Site
        result = unreal.EditorDialog.show_message(
            "Warning", "Generating Widget Blueprint depends on psd_tools library, "
            "download from pypi?\n",
            unreal.AppMsgType.OK_CANCEL, unreal.AppReturnType.OK
        )
        if result == unreal.AppReturnType.CANCEL:
            unreal.log("Abort the Generation of WBP from PSD, "
                       "Reason: psd_tools library does not exist. "
                       "User downloading canceled.")
            return False
        # Download and Install psd_tools
        return download_dependencies()


def reload_module():
    """
    For test AutoPSDUI python code without reboot engine.
    """
    for module_name in sys.modules:
        if module_name.startswith("AutoPSDUI"):
            reload(sys.modules[module_name])


def parse_args():
    """
    Parse cmd args
    """
    opts, args = getopt.getopt(sys.argv[1:], "i:o:", ["input=", "output="])

    input_file = None
    output_asset = None

    for k, v in opts:
        if k in ("-i", "--input"):
            input_file = v
        elif k in ("-o", "--output"):
            output_asset = v
    return input_file, output_asset


def fix_names(psd_content, name_set):
    """
    Ensure that there is no widgets with the same name
    """
    layer_name = psd_content["Name"]

    index = 1
    if layer_name in name_set:
        layer_name = psd_content["Name"] + "_" + str(index)
        index += 1

    psd_content["Name"] = layer_name
    name_set.add(layer_name)

    if "Children" in psd_content:
        for child in psd_content["Children"]:
            fix_names(child, name_set)


def get_image_dst_path(image_path):
    """
    Obtain the imported asset path through the absolute path of the image
    """
    base_name = os.path.basename(image_path)
    base_name = base_name.split(".")[0]
    return "%s/%s" % \
           (psd_gui_setting.texture_asset_dir.path,
            base_name)


def gather_psd_images(p_psd_content, image_list, invalid_image_list):
    """
    Collect all pictures in a PSD structure
    """
    if p_psd_content["Type"] == "Image":
        image_link = p_psd_content["Link"]
        if os.path.exists(image_link):
            image_list.add(image_link)
        else:
            invalid_image_list.add(image_link)
    elif p_psd_content["Type"] == "Button":
        image_link_normal = p_psd_content["LinkNormal"]
        image_link_hovered = p_psd_content["LinkHovered"]
        image_link_pressed = p_psd_content["LinkPressed"]
        image_link_disabled = p_psd_content["LinkDisabled"]
        if image_link_normal:
            if os.path.exists(image_link_normal):
                image_list.add(image_link_normal)
            else:
                invalid_image_list.add(image_link_normal)
        if image_link_hovered:
            if os.path.exists(image_link_hovered):
                image_list.add(image_link_hovered)
            else:
                invalid_image_list.add(image_link_hovered)

        if image_link_pressed:
            if os.path.exists(image_link_pressed):
                image_list.add(image_link_pressed)
            else:
                invalid_image_list.add(image_link_pressed)

        if image_link_disabled:
            if os.path.exists(image_link_disabled):
                image_list.add(image_link_disabled)
            else:
                invalid_image_list.add(image_link_disabled)
    elif p_psd_content["Type"] == "ProgressBar":
        image_link_bg = p_psd_content["BgLink"]
        image_link_fill = p_psd_content["FLink"]
        if image_link_bg:
            if os.path.exists(image_link_bg):
                image_list.add(image_link_bg)
            else:
                invalid_image_list.add(image_link_bg)

        if image_link_fill:
            if os.path.exists(image_link_fill):
                image_list.add(image_link_fill)
            else:
                invalid_image_list.add(image_link_fill)
    if "Children" in p_psd_content:
        for Child in p_psd_content["Children"]:
            gather_psd_images(Child, image_list, invalid_image_list)

    # Gather images of List and Tile View
    if "Child" in p_psd_content:
        if p_psd_content["Child"]:
            gather_psd_images(p_psd_content["Child"], image_list, invalid_image_list)


def import_images(image_list):
    tasks = []
    for image_src in image_list:
        image_dst = psd_gui_setting.texture_asset_dir.path
        task = unreal.AssetImportTask()

        task.filename = image_src
        task.destination_path = image_dst
        task.automated = True
        task.save = True
        tasks.append(task)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)


def gather_list_tile_children(p_psd_content, child_layers):
    if "Children" in p_psd_content:
        for child in p_psd_content["Children"]:
            gather_list_tile_children(child, child_layers)

    if p_psd_content["Type"] in ("ListView", "TileView"):
        child = p_psd_content["Child"]
        if child:
            gather_list_tile_children(child, child_layers)
        child_layers.append(child)


def fix_image_link(p_psd_content):
    if p_psd_content["Type"] == "Image":
        image_link = p_psd_content["Link"]
        fixed_link = get_image_dst_path(image_link)
        p_psd_content["Link"] = fixed_link
    elif p_psd_content["Type"] == "Button":
        image_link_normal = p_psd_content["LinkNormal"]
        image_link_hovered = p_psd_content["LinkHovered"]
        image_link_pressed = p_psd_content["LinkPressed"]
        image_link_disabled = p_psd_content["LinkDisabled"]
        if image_link_normal:
            p_psd_content["LinkNormal"] = get_image_dst_path(image_link_normal)
        if image_link_hovered:
            p_psd_content["LinkHovered"] = get_image_dst_path(image_link_hovered)
        if image_link_pressed:
            p_psd_content["LinkPressed"] = get_image_dst_path(image_link_pressed)
        if image_link_disabled:
            p_psd_content["LinkDisabled"] = get_image_dst_path(image_link_disabled)
    elif p_psd_content["Type"] == "ProgressBar":
        image_link_bg = p_psd_content["BgLink"]
        image_link_fill = p_psd_content["FLink"]
        if image_link_bg:
            p_psd_content["BgLink"] = get_image_dst_path(image_link_bg)
        if image_link_fill:
            p_psd_content["FLink"] = get_image_dst_path(image_link_fill)
    if "Children" in p_psd_content:
        for Child in p_psd_content["Children"]:
            fix_image_link(Child)

    # fix image links of list view and tile view
    if "Child" in p_psd_content:
        if p_psd_content["Child"]:
            fix_image_link(p_psd_content["Child"])


def process_child_layer(p_child_layer, parent_widget, wbp_obj):
    if p_child_layer["Type"] == "Canvas":
        create_canvas(p_child_layer, parent_widget, wbp_obj)
    elif p_child_layer["Type"] == "Button":
        create_button(p_child_layer, parent_widget, wbp_obj)
    elif p_child_layer["Type"] == "Image":
        create_image(p_child_layer, parent_widget, wbp_obj)
    elif p_child_layer["Type"] == "Text":
        create_text(p_child_layer, parent_widget, wbp_obj)
    elif p_child_layer["Type"] == "ProgressBar":
        create_progress_bar(p_child_layer, parent_widget, wbp_obj)
    elif p_child_layer["Type"] == "ListView":
        create_list_view(p_child_layer, parent_widget, wbp_obj)
    elif p_child_layer["Type"] == "TileView":
        create_tile_view(p_child_layer, parent_widget, wbp_obj)


def process_parent_widget(p_layer, p_widget, parent_widget):
    if parent_widget:
        slot = parent_widget.add_child(p_widget)
        x = p_layer["X"]
        y = p_layer["Y"]
        width = p_layer["Width"]
        height = p_layer["Height"]

        slot.set_position(unreal.Vector2D(x, y))
        slot.set_size(unreal.Vector2D(width, height))


def create_widgets_for_wbp(p_psd_content, wbp_object):
    root_widget = create_canvas(p_psd_content, None, wbp_object)
    if root_widget:
        unreal.AutoPSDUILibrary.set_wbp_root_widget(wbp_object, root_widget)


def create_canvas(p_layer_content, parent_widget, wbp_object):
    if p_layer_content["Type"] != "Canvas":
        return None

    widget_name = p_layer_content["Name"]
    canvas_widget = unreal.AutoPSDUILibrary.make_widget_with_wbp(unreal.CanvasPanel.static_class(), wbp_object, widget_name)

    process_parent_widget(p_layer_content, canvas_widget, parent_widget)

    for child in p_layer_content["Children"]:
        process_child_layer(child, canvas_widget, wbp_object)
    return canvas_widget


def create_text(p_text_content, parent_widget, wbp_object):
    if p_text_content["Type"] != "Text":
        return None

    widget_name = p_text_content["Name"]
    text_widget = unreal.AutoPSDUILibrary.make_widget_with_wbp(unreal.TextBlock.static_class(), wbp_object, widget_name)

    process_parent_widget(p_text_content, text_widget, parent_widget)

    text_widget.set_text(p_text_content["Text"])
    color_r = p_text_content["ColorR"]
    color_g = p_text_content["ColorG"]
    color_b = p_text_content["ColorB"]
    color_a = p_text_content["ColorA"]
    size = p_text_content["Size"]
    alignment = p_text_content["Alignment"]

    text_widget.set_color_and_opacity(unreal.SlateColor(unreal.LinearColor(color_r, color_g, color_b, color_a)))

    font_info = unreal.SlateFontInfo()

    # Process Font
    font_name = p_text_content["Font"]
    if font_name in font_map:
        font_info.font_object = font_map[font_name]
    else:
        font_info.font_object = default_font

    font_info.size = size
    if p_text_content["StrokeEnabled"]:
        stroke_color_r = p_text_content["StrokeColorR"]
        stroke_color_g = p_text_content["StrokeColorG"]
        stroke_color_b = p_text_content["StrokeColorB"]
        stroke_color_a = p_text_content["StrokeColorA"]

        font_info.outline_settings.outline_color = unreal.LinearColor(
            stroke_color_r, stroke_color_g, stroke_color_b, stroke_color_a
        )
        font_info.outline_settings.outline_size = p_text_content["StrokeSize"]

    text_widget.set_font(font_info)

    # Alignment
    if alignment == "Left":
        text_widget.justification = unreal.TextJustify.LEFT
    elif alignment == "Right":
        text_widget.justification = unreal.TextJustify.RIGHT
    elif alignment == "Center":
        text_widget.justification = unreal.TextJustify.CENTER

    if p_text_content["ShadowEnabled"]:
        shadow_color_r = p_text_content["ShadowColorR"]
        shadow_color_g = p_text_content["ShadowColorG"]
        shadow_color_b = p_text_content["ShadowColorB"]
        shadow_color_a = p_text_content["ShadowColorA"]

        offset_x = p_text_content["ShadowOffsetX"]
        offset_y = p_text_content["ShadowOffsetY"]

        text_widget.set_shadow_color_and_opacity(
            unreal.LinearColor(shadow_color_r, shadow_color_g, shadow_color_b, shadow_color_a)
        )
        text_widget.set_shadow_offset(unreal.Vector2D(offset_x, offset_y))

    return text_widget


def create_image(p_image_content, parent_widget, wbp_object):
    if p_image_content["Type"] != "Image":
        return None
    widget_name = p_image_content["Name"]
    image_widget = unreal.AutoPSDUILibrary.make_widget_with_wbp(unreal.Image.static_class(), wbp_object, widget_name)

    process_parent_widget(p_image_content, image_widget, parent_widget)

    brush = unreal.SlateBrush()
    link_image = p_image_content["Link"]
    if link_image:
        link_image_obj = unreal.EditorAssetLibrary.load_asset(link_image)
        if link_image_obj:

            brush.resource_object = link_image_obj
    image_widget.set_brush(brush)

    if p_image_content["bColorOverlay"]:
        color_r = p_image_content["ColorOverlayR"]
        color_g = p_image_content["ColorOverlayG"]
        color_b = p_image_content["ColorOverlayB"]
        color_a = p_image_content["ColorOverlayA"]
        image_widget.set_color_and_opacity(unreal.LinearColor(color_r, color_g, color_b, color_a))

    return image_widget


def create_button(p_button_content, parent_widget, wbp_object):
    if p_button_content["Type"] != "Button":
        return None
    widget_name = p_button_content["Name"]
    button_widget = unreal.AutoPSDUILibrary.make_widget_with_wbp(unreal.Button.static_class(), wbp_object, widget_name)

    process_parent_widget(p_button_content, button_widget, parent_widget)

    # Set Style
    button_style = unreal.ButtonStyle()

    # Normal Brush
    normal_brush = unreal.SlateBrush()
    link_normal = p_button_content["LinkNormal"]
    if link_normal:
        link_obj = unreal.EditorAssetLibrary.load_asset(link_normal)
        if link_obj:
            normal_brush.resource_object = link_obj
    button_style.normal = normal_brush

    # hovered
    hovered_brush = unreal.SlateBrush()
    link_hovered = p_button_content["LinkHovered"]
    if link_hovered:
        link_obj = unreal.EditorAssetLibrary.load_asset(link_hovered)
        if link_obj:
            hovered_brush.resource_object = link_obj
    button_style.hovered = normal_brush

    # pressed
    pressed_brush = unreal.SlateBrush()
    link_pressed = p_button_content["LinkPressed"]
    if link_pressed:
        link_obj = unreal.EditorAssetLibrary.load_asset(link_pressed)
        if link_obj:
            pressed_brush.resource_object = link_obj
    button_style.pressed = normal_brush

    # disabled
    disabled_brush = unreal.SlateBrush()
    link_disabled = p_button_content["LinkDisabled"]
    if link_disabled:
        link_obj = unreal.EditorAssetLibrary.load_asset(link_disabled)
        if link_obj:
            disabled_brush.resource_object = link_obj
    button_style.disabled = normal_brush
    button_widget.set_style(button_style)

    if "Children" in p_button_content:
        children = p_button_content["Children"]
        if len(children) != 0:
            # Add a canvas as other widgets' parent widget
            child_canvas_name = widget_name + "_canvas"
            child_canvas_widget = unreal.AutoPSDUILibrary.make_widget_with_wbp(
                unreal.CanvasPanel.static_class(), wbp_object, child_canvas_name
            )
            button_slot = button_widget.add_child(child_canvas_widget)
            button_slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
            button_slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_FILL)

            process_child_layer(children[0], child_canvas_widget, wbp_object)

    return button_widget


def create_progress_bar(p_progress_content, parent_widget, wbp_object):
    if p_progress_content["Type"] != "ProgressBar":
        return None

    widget_name = p_progress_content["Name"]
    progress_widget = unreal.AutoPSDUILibrary.make_widget_with_wbp(
        unreal.ProgressBar.static_class(), wbp_object, widget_name
    )
    process_parent_widget(p_progress_content, progress_widget, parent_widget)

    # Set Style
    progress_style = unreal.ProgressBarStyle()

    # Background
    bg_brush = unreal.SlateBrush()
    bg_link = p_progress_content["BgLink"]

    if bg_link:
        link_obj = unreal.EditorAssetLibrary.load_asset(bg_link)
        if link_obj:
            bg_brush.resource_object = link_obj
    progress_style.background_image = bg_brush

    # fill_image
    fill_brush = unreal.SlateBrush()
    fill_link = p_progress_content["FLink"]
    if fill_link:
        link_obj = unreal.EditorAssetLibrary.load_asset(fill_link)
        if link_obj:
            fill_brush.resource_object = link_obj
    progress_style.fill_image = fill_brush

    progress_widget.widget_style = progress_style


def create_list_view(p_list_content, parent_widget, wbp_object):
    if p_list_content["Type"] != "ListView":
        return None

    widget_name = p_list_content["Name"]
    list_widget = unreal.AutoPSDUILibrary.make_widget_with_wbp(
        unreal.ListView.static_class(), wbp_object, widget_name
    )
    process_parent_widget(p_list_content, list_widget, parent_widget)

    # Set Child Class
    if p_list_content["Child"]:
        child_layer = p_list_content["Child"]
        child_wbp_asset = os.path.join(dst_path, child_layer["Name"])
        if unreal.EditorAssetLibrary.does_asset_exist(child_wbp_asset):
            child_wbp = unreal.EditorAssetLibrary.load_asset(child_wbp_asset)
            if child_wbp:
                list_widget.set_editor_property(
                    "EntryWidgetClass", unreal.AutoPSDUILibrary.get_bp_generated_class(child_wbp)
                )


def create_tile_view(p_tile_layer, parent_widget, wbp_object):
    if p_tile_layer["Type"] != "TileView":
        return None

    widget_name = p_tile_layer["Name"]
    tile_widget = unreal.AutoPSDUILibrary.make_widget_with_wbp(
        unreal.TileView.static_class(), wbp_object, widget_name
    )
    process_parent_widget(p_tile_layer, tile_widget, parent_widget)

    # Set Child Class
    if p_tile_layer["Child"]:
        child_layer = p_tile_layer["Child"]
        child_wbp_asset = os.path.join(dst_path, child_layer["Name"])
        if unreal.EditorAssetLibrary.does_asset_exist(child_wbp_asset):
            child_wbp = unreal.EditorAssetLibrary.load_asset(child_wbp_asset)
            if child_wbp:
                tile_widget.set_editor_property(
                    "EntryWidgetClass", unreal.AutoPSDUILibrary.get_bp_generated_class(child_wbp)
                )
                tile_widget.set_entry_height(child_layer["Height"])
                tile_widget.set_entry_width(child_layer["Width"])


def main():
    psd_file, wbp_asset = parse_args()
    global dst_path
    dst_path = os.path.dirname(wbp_asset)

    psd = load_psd(psd_file)

    """
    1. Parse PSD File
    2. Fix Names
    3. Process Image and Fix Image Link
    4. Create WBP
    5. Create Widget for WBP
    """
    image_layers = {}
    content_name = ".".join(os.path.basename(psd_file).split(".")[:-1])
    content = parse_psd(psd)
    content["Name"] = content_name

    # Process Names
    name_set = set()
    fix_names(content, name_set)

    # Process Images
    images = set()
    invalid_images = set()
    gather_psd_images(content, images, invalid_images)
    import_images(images)
    fix_image_link(content)

    # Process Child Widget Blueprint
    child_layers = []
    gather_list_tile_children(content, child_layers)
    for child_layer in child_layers:
        child_wbp_asset = os.path.join(dst_path, child_layer["Name"])

        if unreal.EditorAssetLibrary.does_asset_exist(child_wbp_asset):
            child_created_wbp = unreal.EditorAssetLibrary.load_asset(child_wbp_asset)
        else:
            child_created_wbp = unreal.AutoPSDUILibrary.create_wbp(child_wbp_asset)

        create_widgets_for_wbp(child_layer, child_created_wbp)
        # Apply ListEntryInterface
        unreal.AutoPSDUILibrary.apply_interface_to_bp(child_created_wbp, unreal.UserObjectListEntry.static_class())
        unreal.AutoPSDUILibrary.compile_and_save_bp(child_created_wbp)

    # Create WBP
    if unreal.EditorAssetLibrary.does_asset_exist(wbp_asset):
        created_wbp = unreal.EditorAssetLibrary.load_asset(wbp_asset)
    else:
        created_wbp = unreal.AutoPSDUILibrary.create_wbp(wbp_asset)
    create_widgets_for_wbp(content, created_wbp)
    unreal.AutoPSDUILibrary.compile_and_save_bp(created_wbp)


if __name__ == "__main__":
    reload_module()
    # this must be front of other AutoPSDUI module
    from AutoPSDUI import common
    from AutoPSDUI.common import download_dependencies

    if check_psd_tools():
        from AutoPSDUI.common import psd_gui_setting
        from AutoPSDUI.psd_utils import load_psd
        from AutoPSDUI.psd_utils import parse_psd
        main()
