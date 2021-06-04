import os
import math
from psd_tools import PSDImage
from psd_tools.api import layers as Layers
from psd_tools.api import effects as Effects

import unreal

texture_src_dir = unreal.AutoPSDUISetting.get().texture_src_dir.path


if not os.path.exists(texture_src_dir):
    os.makedirs(texture_src_dir)


def export_image(p_layer: Layers.PixelLayer, dst_path):
    base_dir = os.path.dirname(dst_path)
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)
    p_layer.composite().save(dst_path)


def load_psd(p_psd_file: str):
    if not os.path.exists(p_psd_file):
        return None

    psd_content = PSDImage.open(p_psd_file)
    return psd_content


def get_layer_pos_size(p_psd_layer, parent):
    x = p_psd_layer.left
    y = p_psd_layer.top
    if parent and "AbsX" in parent:
        x = x - parent["AbsX"]
    if parent and "AbsY" in parent:
        y = y - parent["AbsY"]
    width = p_psd_layer.width
    height = p_psd_layer.height
    return x, y, width, height


def process_child_layer(p_child_layer, p_parent_layer):
    if p_child_layer.kind == "group":
        child = parse_layer(p_child_layer, p_parent_layer)
    elif p_child_layer.kind in ("pixel", "smartobject", "shape"):
        child = parse_image(p_child_layer, p_parent_layer)
    elif p_child_layer.kind == "type":
        child = parse_text(p_child_layer, p_parent_layer)
    else:
        unreal.log_warning("Unknown PSD Layer Type: %s" % p_child_layer.kind)
        child = None
    return child


def process_layer(p_layer_content: Layers.Layer, layer_info):
    if "Children" not in layer_info:
        layer_info["Children"] = []
    for layer in p_layer_content:
        child = process_child_layer(layer, layer_info)
        if child:
            layer_info["Children"].append(child)


def parse_psd(p_psd_content: PSDImage):
    x, y, width, height = get_layer_pos_size(p_psd_content, None)
    layer_info = {
        "Type": "Canvas",
        "X": x,
        "Y": y,
        "AbsX": p_psd_content.left,
        "AbsY": p_psd_content.top,
        "Width": width,
        "Height": height,
        "Children": []
    }
    process_layer(p_psd_content, layer_info)
    return layer_info


def parse_layer(p_layer_content: Layers.Layer, parent):
    if p_layer_content.kind != "group":
        return None

    layer_name = p_layer_content.name
    x, y, width, height = get_layer_pos_size(p_layer_content, parent)
    layer_info = {
        "Type": "Canvas",
        "Name": layer_name,
        "X": x,
        "Y": y,
        "AbsX": p_layer_content.left,
        "AbsY": p_layer_content.top,
        "Width": width,
        "Height": height,
        "Children": []
    }

    if layer_name.startswith("Button_"):
        parse_button(p_layer_content, layer_info)
    elif layer_name.startswith("Progress_"):
        parse_progress_bar(p_layer_content, layer_info)
    elif layer_name.startswith("List_"):
        parse_list(p_layer_content, layer_info, parent)
    elif layer_name.startswith("Tile_"):
        parse_tile(p_layer_content, layer_info, parent)
    else:
        # 其他情况均按照Canvas处理
        process_layer(p_layer_content, layer_info)

    return layer_info


def parse_button(p_layer_content: Layers.Layer, p_button_info):
    p_button_info["Type"] = "Button"
    p_button_info["LinkNormal"] = None
    p_button_info["bNormalColorOverlay"] = False
    p_button_info["LinkNormalColorR"] = None
    p_button_info["LinkNormalColorG"] = None
    p_button_info["LinkNormalColorB"] = None
    p_button_info["LinkNormalColorA"] = None

    p_button_info["LinkHovered"] = None
    p_button_info["bHoveredColorOverlay"] = False
    p_button_info["LinkHoveredColorR"] = None
    p_button_info["LinkHoveredColorG"] = None
    p_button_info["LinkHoveredColorB"] = None
    p_button_info["LinkHoveredColorA"] = None

    p_button_info["LinkPressed"] = None
    p_button_info["bPressedColorOverlay"] = False
    p_button_info["LinkPressedColorR"] = None
    p_button_info["LinkPressedColorG"] = None
    p_button_info["LinkPressedColorB"] = None
    p_button_info["LinkPressedColorA"] = None

    p_button_info["LinkDisabled"] = None
    p_button_info["bDisabledColorOverlay"] = False
    p_button_info["LinkDisabledColorR"] = None
    p_button_info["LinkDisabledColorG"] = None
    p_button_info["LinkDisabledColorB"] = None
    p_button_info["LinkDisabledColorA"] = None
    children = []
    for layer in p_layer_content:
        layer_name = layer.name
        valid_image = False
        image_type = ""

        if layer.kind in ("pixel", "smartobject", "shape"):
            if layer_name.endswith("_normal"):
                p_button_info["LinkNormal"] = os.path.join(texture_src_dir, layer_name[:-7]) + ".png"
                export_image(layer, p_button_info["LinkNormal"])
                valid_image = True
                image_type = "normal"
            elif layer_name.endswith("_hovered"):
                p_button_info["LinkHovered"] = os.path.join(texture_src_dir, layer_name[:-8]) + ".png"
                export_image(layer, p_button_info["LinkHovered"])
                valid_image = True
                image_type = "hovered"
            elif layer_name.endswith("_pressed"):
                p_button_info["LinkPressed"] = os.path.join(texture_src_dir, layer_name[:-8]) + ".png"
                export_image(layer, p_button_info["LinkPressed"])
                valid_image = True
                image_type = "pressed"
            elif layer_name.endswith("_disabled"):
                p_button_info["LinkDisabled"] = os.path.join(texture_src_dir, layer_name[:-9]) + ".png"
                export_image(layer, p_button_info["LinkDisabled"])
                valid_image = True
                image_type = "disabled"

        if not valid_image:
            child = process_child_layer(layer, p_button_info)
            if child:
                children.append(child)
        else:
            effects = layer.effects
            for effect in effects:
                if isinstance(effect, Effects.ColorOverlay):
                    if effect.blend_mode == b"Mltp":
                        color = effect.color
                        color_r = color[b'Rd  '] / 255
                        color_g = color[b'Grn '] / 255
                        color_b = color[b'Bl  '] / 255
                        color_a = effect.opacity / 100
                        if image_type == "normal":
                            p_button_info["bNormalColorOverlay"] = True
                            p_button_info["LinkNormalColorR"] = color_r
                            p_button_info["LinkNormalColorG"] = color_g
                            p_button_info["LinkNormalColorB"] = color_b
                            p_button_info["LinkNormalColorA"] = color_a
                        elif image_type == "hovered":
                            p_button_info["bHoveredColorOverlay"] = True
                            p_button_info["LinkHoveredColorR"] = color_r
                            p_button_info["LinkHoveredColorG"] = color_g
                            p_button_info["LinkHoveredColorB"] = color_b
                            p_button_info["LinkHoveredColorA"] = color_a
                        elif image_type == "pressed":
                            p_button_info["bPressedColorOverlay"] = True
                            p_button_info["LinkPressedColorR"] = color_r
                            p_button_info["LinkPressedColorG"] = color_g
                            p_button_info["LinkPressedColorB"] = color_b
                            p_button_info["LinkPressedColorA"] = color_a
                        elif image_type == "disabled":
                            p_button_info["bDisabledColorOverlay"] = True
                            p_button_info["LinkDisabledColorR"] = color_r
                            p_button_info["LinkDisabledColorG"] = color_g
                            p_button_info["LinkDisabledColorB"] = color_b
                            p_button_info["LinkDisabledColorA"] = color_a
                    else:
                        unreal.log_warning("UnSupported ColorOverlay Effect Blend Mode '%s' for Image '%s'" % (
                        effect.blend_mode.decode(), layer_name))

    p_button_info["Children"] = children
    return p_button_info


def parse_image(p_image_layer: Layers.PixelLayer, parent):
    x, y, width, height = get_layer_pos_size(p_image_layer, parent)

    name = p_image_layer.name
    image_info = {
        "Type": "Image",
        "Name": name,
        "X": x,
        "Y": y,
        "AbsX": p_image_layer.left,
        "AbsY": p_image_layer.top,
        "Width": width,
        "Height": height,
        "Link": os.path.join(texture_src_dir, name) + ".png",
        "bColorOverlay": False,
        "ColorOverlayR": 1.0,
        "ColorOverlayG": 1.0,
        "ColorOverlayB": 1.0,
        "ColorOverlayA": 1.0
    }
    export_image(p_image_layer, image_info["Link"])

    # 处理颜色叠加
    effects = p_image_layer.effects

    for effect in effects:
        if isinstance(effect, Effects.ColorOverlay):
            if effect.blend_mode == b"Mltp":
                image_info["bColorOverlay"] = True
                color = effect.color
                image_info["ColorOverlayR"] = color[b'Rd  '] / 255
                image_info["ColorOverlayG"] = color[b'Grn '] / 255
                image_info["ColorOverlayB"] = color[b'Bl  '] / 255
                image_info["ColorOverlayA"] = effect.opacity / 100
            else:
                unreal.log_warning("UnSupported ColorOverlay Effect Blend Mode '%s' for Image '%s'" % (
                    effect.blend_mode.decode(), name))

    return image_info


def parse_text(p_psd_text_layer: Layers.TypeLayer, parent):
    if p_psd_text_layer.kind != "type":
        return None

    x, y, width, height = get_layer_pos_size(p_psd_text_layer, parent)
    text_info = {
        "Type": "Text",
        "Name": p_psd_text_layer.name,
        "X": x,
        "Y": y,
        "AbsX": p_psd_text_layer.left,
        "AbsY": p_psd_text_layer.top,
        "Width": width,
        "Height": height
    }

    text = p_psd_text_layer.text
    opacity = p_psd_text_layer.opacity

    resource_dict = p_psd_text_layer.resource_dict

    color = resource_dict["StyleSheetSet"][0]["StyleSheetData"]["FillColor"]["Values"]
    size = resource_dict["StyleSheetSet"][0]["StyleSheetData"]["FontSize"]

    font_index = resource_dict["StyleSheetSet"][0]["StyleSheetData"]["Font"]
    font = str(resource_dict["FontSet"][font_index]["Name"]).replace("'", "").replace("\"", "")
    # 描边 & 阴影
    stroke = {
        "enabled": False,
        "color": None,
        "size": None,
        "opacity": None
    }
    drop_shadow = {
        "enabled": False,
        "color": None,
        "opacity": None,
        "distance": None,
        "angle": None
    }
    effects = p_psd_text_layer.effects
    for effect in effects:
        if isinstance(effect, Effects.Stroke):
            stroke["enabled"] = effect.enabled
            stroke["color"] = effect.color
            stroke["size"] = effect.size
            stroke["opacity"] = effect.opacity
        elif isinstance(effect, Effects.DropShadow):
            drop_shadow["enabled"] = effect.enabled
            drop_shadow["color"] = effect.color
            drop_shadow["opacity"] = effect.opacity
            drop_shadow["distance"] = effect.distance
            drop_shadow["angle"] = effect.angle

    engine_dict = p_psd_text_layer.engine_dict
    alignment = engine_dict["ParagraphRun"]["RunArray"][0]["ParagraphSheet"]["Properties"]["Justification"]

    text_info["Text"] = text

    text_info["ColorR"] = color[0] / 255
    text_info["ColorG"] = color[1] / 255
    text_info["ColorB"] = color[2] / 255
    text_info["ColorA"] = opacity / 255
    # It seems like the size of text in ue is bigger 2 than PS
    text_info["Size"] = int(size) - 2
    text_info["Font"] = font
    text_info["Alignment"] = "Left"
    text_info["StrokeEnabled"] = stroke["enabled"]
    text_info["StrokeColorR"] = 1.0
    text_info["StrokeColorG"] = 1.0
    text_info["StrokeColorB"] = 1.0
    text_info["StrokeColorA"] = 1.0
    text_info["StrokeSize"] = 1
    text_info["ShadowEnabled"] = drop_shadow["enabled"]
    text_info["ShadowColorR"] = 1.0
    text_info["ShadowColorG"] = 1.0
    text_info["ShadowColorB"] = 1.0
    text_info["ShadowColorA"] = 1.0
    text_info["ShadowOffsetX"] = 0
    text_info["ShadowOffsetY"] = 0

    if stroke["enabled"]:
        text_info["StrokeColorR"] = stroke["color"][b"Rd  "] / 255
        text_info["StrokeColorG"] = stroke["color"][b"Grn "] / 255
        text_info["StrokeColorB"] = stroke["color"][b"Bl  "] / 255
        text_info["StrokeColorA"] = stroke["opacity"] / 100
        text_info["StrokeSize"] = int(stroke["size"])

    if drop_shadow["enabled"]:
        text_info["ShadowColorR"] = drop_shadow["color"][b"Rd  "] / 255
        text_info["ShadowColorG"] = drop_shadow["color"][b"Grn "] / 255
        text_info["ShadowColorB"] = drop_shadow["color"][b"Bl  "] / 255
        text_info["ShadowColorA"] = drop_shadow["opacity"] / 100

        text_info["ShadowOffsetY"] = int(drop_shadow["distance"] * math.sin(drop_shadow["angle"] / 180 * math.pi))
        text_info["ShadowOffsetX"] = -int(drop_shadow["distance"] * math.cos(drop_shadow["angle"] / 180 * math.pi))

        # Fix position
        text_info["X"] += text_info["ShadowOffsetX"] / 2
        text_info["Y"] += text_info["ShadowOffsetY"] / 2

    if alignment == 0:
        text_info["Alignment"] = "Left"
    elif alignment == 1:
        text_info["Alignment"] = "Right"
    elif alignment == 2:
        text_info["Alignment"] = "Center"

    return text_info


def parse_progress_bar(p_layer_content: Layers.Layer, p_progress_info):
    p_progress_info["Type"] = "ProgressBar"
    p_progress_info["BgLink"] = None
    p_progress_info["bBgColorOverlay"] = False
    p_progress_info["BgColorR"] = 0.0
    p_progress_info["BgColorG"] = 0.0
    p_progress_info["BgColorB"] = 0.0
    p_progress_info["BgColorA"] = 0.0

    p_progress_info["FLink"] = None
    p_progress_info["bFColorOverlay"] = False
    p_progress_info["FColorR"] = 0.0
    p_progress_info["FColorG"] = 0.0
    p_progress_info["FColorB"] = 0.0
    p_progress_info["FColorA"] = 0.0

    for layer in p_layer_content:
        layer_name = layer.name
        valid_image = False
        image_type = ""
        print(layer.kind)
        if layer.kind in ("pixel", "smartobject", "shape"):
            if layer_name.endswith("_background"):
                p_progress_info["BgLink"] = os.path.join(texture_src_dir, layer_name[:-11]) + ".png"
                export_image(layer, p_progress_info["BgLink"])
                valid_image = True
                image_type = "background"
            elif layer_name.endswith("_fill"):
                p_progress_info["FLink"] = os.path.join(texture_src_dir, layer_name[:-11]) + ".png"
                export_image(layer, p_progress_info["FLink"])
                valid_image = True
                image_type = "fill"

        if valid_image:
            effects = layer.effects
            for effect in effects:
                if isinstance(effect, Effects.ColorOverlay):
                    if effect.blend_mode == b"Mltp":
                        color = effect.color
                        color_r = color[b'Rd  '] / 255
                        color_g = color[b'Grn '] / 255
                        color_b = color[b'Bl  '] / 255
                        color_a = effect.opacity / 100
                        if image_type == "background":
                            p_progress_info["bBgColorOverlay"] = True
                            p_progress_info["BgColorR"] = color_r
                            p_progress_info["BgColorG"] = color_g
                            p_progress_info["BgColorB"] = color_b
                            p_progress_info["BgColorA"] = color_a
                        elif image_type == "fill":
                            p_progress_info["bFColorOverlay"] = False
                            p_progress_info["FColorR"] = color_r
                            p_progress_info["FColorG"] = color_g
                            p_progress_info["FColorB"] = color_b
                            p_progress_info["FColorA"] = color_a

    return p_progress_info


def parse_list(p_layer_content: Layers.Layer, p_list_info, parent):
    p_list_info["Type"] = "ListView"
    p_list_info["Child"] = None

    # The size is the same with parent
    if parent:
        p_list_info["Width"] = parent["Width"] - p_list_info["X"] * 2
        p_list_info["Height"] = parent["Height"] - p_list_info["Y"] * 2

    child_layer = None
    for layer in p_layer_content:
        if layer.name == "child" and layer.kind == "group":
            child_layer = layer
    if not child_layer:
        unreal.log_warning(
            "Cannot detect the child layer of list view layer : %s."
            "the child layer should named with 'child' and must be a group." % p_list_info["Name"]
        )
        return p_list_info

    child = process_child_layer(child_layer, p_list_info)
    if child:
        child["Name"] = p_list_info["Name"] + "_item"
        p_list_info["Child"] = child

        child["X"] = 0
        child["Y"] = 0
    return p_list_info


def parse_tile(p_layer_content: Layers.Layer, p_tile_info, parent):
    p_tile_info["Type"] = "TileView"
    p_tile_info["Child"] = None

    # The size is the same with parent
    if parent:
        p_tile_info["Width"] = parent["Width"] - p_tile_info["X"] * 2
        p_tile_info["Height"] = parent["Height"] - p_tile_info["Y"] * 2

    child_layer = None
    for layer in p_layer_content:
        if layer.name == "child" and layer.kind == "group":
            child_layer = layer
    if not child_layer:
        unreal.log_warning(
            "Cannot detect the child layer of tile view layer : %s."
            "the child layer should named with 'child' and must be a group." % p_tile_info["Name"]
        )
        return p_tile_info

    child = process_child_layer(child_layer, p_tile_info)
    if child:
        child["Name"] = p_tile_info["Name"] + "_item"
        p_tile_info["Child"] = child

        child["X"] = 0
        child["Y"] = 0

    return p_tile_info
