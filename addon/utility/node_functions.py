import colorsys
import bpy

from typing import Any

from bpy.types import (NodeSocket,
                       Node,
                       NodeLink,
                       NodeSocket,
                       NodeTree
                       )


def create_node(node_tree: NodeTree, bl_idname: str, location: list[float] = [0, 0]) -> Node:
    '''Create new node using original node as reference'''

    node = node_tree.nodes.new(bl_idname)
    node.location = location

    return node


def create_node_link(node_tree: NodeTree, link1: NodeSocket, link2: NodeSocket) -> None:
    '''Create Node Link'''

    link = node_tree.links.new
    link(link1, link2)


def replace_node(original_node: Node, replace_bl_idname: str, input_replace: dict, output_replace: dict) -> Node:
    '''Create a new node, update the links from the old node, and deletes it'''

    replacement_node = create_node(
        original_node.id_data, replace_bl_idname, original_node.location)

    if input_replace:
        for i in input_replace:
            if original_node.inputs[int(i)].links:
                create_node_link(
                    original_node.id_data, original_node.inputs[int(i)].links[0].from_socket, replacement_node.inputs[input_replace[i]])

    if output_replace:
        for i in output_replace:
            for link in original_node.outputs[int(i)].links:
                create_node_link(
                    original_node.id_data, link.to_socket, replacement_node.outputs[output_replace[i]])

    return replacement_node


def move_node_link_to_socket(node_socket: NodeSocket, to_socket_index: int) -> None:
    '''Move a link from NodeSocket to another index'''

    node = node_socket.node
    node_tree = node.id_data

    for link in node_socket.links:
        if link.from_node == node:  # Meaning that is an output node
            create_node_link(
                node.id_data, node.outputs[to_socket_index], link.to_socket)
        else:
            create_node_link(
                node.id_data, link.from_socket, node.inputs[to_socket_index])

            node_tree.links.remove(link)


def remove_node_and_pass_link_through(node: Node, input_index: int = 0, output_index: int = 0) -> None:
    '''remove inputted node, and pass the link through the input.from_socket to output.from_socket'''

    node_tree = node.id_data

    for link in node.outputs[output_index].links:
        create_node_link(
            node.id_data, node.inputs[input_index].links[0].from_socket, link.to_socket)

    node_tree.nodes.remove(node)

def get_valid_socket_type(socket_type: str) -> str:
    """Konwertuje nazwy socketów na prawidłowe typy akceptowane przez Blender"""
    socket_type_mapping = {
        # Standardowe typy
        'NodeSocketFloat': 'NodeSocketFloat',
        'NodeSocketVector': 'NodeSocketVector',
        'NodeSocketColor': 'NodeSocketColor',
        'NodeSocketBool': 'NodeSocketBool',
        'NodeSocketInt': 'NodeSocketInt',
        'NodeSocketShader': 'NodeSocketShader',
        
        # Konwersja specjalnych typów
        'NodeSocketFloatFactor': 'NodeSocketFloat',
        'NodeSocketFloatAngle': 'NodeSocketFloat',
        'NodeSocketFloatDistance': 'NodeSocketFloat',
        'NodeSocketFloatTime': 'NodeSocketFloat',
        'NodeSocketFloatUnsigned': 'NodeSocketFloat',
        'NodeSocketVectorEuler': 'NodeSocketVector',
        'NodeSocketVectorTranslation': 'NodeSocketVector',
        'NodeSocketVectorXYZ': 'NodeSocketVector'
    }
    
    return socket_type_mapping.get(socket_type, 'NodeSocketFloat')
    
    
def create_null_node(node: Node, node_tree, null_links, group_inputs, group_outputs):
    group_tree = bpy.data.node_groups.new(
        "NULL_NODE_" + node.bl_idname, 'ShaderNodeTree')

    group_in = group_tree.nodes.new('NodeGroupInput')
    group_out = group_tree.nodes.new('NodeGroupOutput')

    # Create inputs
    for socket_name, socket_type in group_inputs.items():
        valid_type = get_valid_socket_type(socket_type)
        new_input = group_tree.interface.new_socket(
            name=socket_name,
            in_out='INPUT',
            socket_type=valid_type
        )
        
        if hasattr(node.inputs.get(socket_name, None), "default_value"):
            try:
                new_input.default_value = node.inputs[socket_name].default_value
            except:
                pass

    # Create outputs
    for socket_name, socket_type in group_outputs.items():
        valid_type = get_valid_socket_type(socket_type)
        group_tree.interface.new_socket(
            name=socket_name,
            in_out='OUTPUT',
            socket_type=valid_type
        )

    group_in.location = (0, 0)
    group_out.location = (200, 0)

    # Handle ShaderNodeBump connections
    if node.bl_idname == "ShaderNodeBump":
        # Always create internal connections
        if "Height" in [socket.name for socket in group_in.outputs] and "Bump" in [socket.name for socket in group_out.inputs]:
            group_tree.links.new(
                group_in.outputs["Height"],
                group_out.inputs["Bump"]
            )
            
        if "Normal" in [socket.name for socket in group_in.outputs] and "Normal" in [socket.name for socket in group_out.inputs]:
            group_tree.links.new(
                group_in.outputs["Normal"],
                group_out.inputs["Normal"]
            )
    else:
        for input_name, output_name in null_links.items():
            if input_name in [socket.name for socket in group_in.outputs] and \
               output_name in [socket.name for socket in group_out.inputs]:
                group_tree.links.new(
                    group_in.outputs[input_name],
                    group_out.inputs[output_name]
                )

    # Create group node
    null_group_node = node_tree.nodes.new('ShaderNodeGroup')
    null_group_node.node_tree = group_tree
    null_group_node.name = "NULL_NODE_" + node.bl_idname
    null_group_node.label = node.name
    null_group_node.location = node.location
    null_group_node.hide = True

    # Connect to Universal Material based on original inputs
    if node.bl_idname == "ShaderNodeBump":
        for output_link in node.outputs["Normal"].links:
            if output_link.to_node.bl_idname == "OctaneUniversalMaterial":
                if node.inputs["Height"].is_linked:
                    node_tree.links.new(
                        null_group_node.outputs["Bump"],
                        output_link.to_node.inputs["Bump"]
                    )
                elif node.inputs["Normal"].is_linked:
                    node_tree.links.new(
                        null_group_node.outputs["Normal"],
                        output_link.to_node.inputs["Normal"]
                    )

    return null_group_node

def convert_old_to_new_socket_value(new_socket: NodeSocket, old_value: Any) -> Any:
    '''correctly convert the old node value, to the new node value'''

    if new_socket.type == "VALUE":
        if isinstance(old_value, (float, int)):
            return old_value

        if isinstance(old_value, bpy.types.bpy_prop_array):
            if len(old_value) == 4:
                return old_value[-2]
            if len(old_value) == 3:
                return old_value[-1]

    if new_socket.type == "RGBA":

        if isinstance(old_value, (float, int)):
            rgb = colorsys.hsv_to_rgb(0.5, 0, old_value)
            rgba = [i for i in rgb]
            rgba.append(1)

            return rgba

        if len(old_value) == 3:
            rgb = list(old_value)
            rgba = [i for i in rgb]
            rgba.append(1)

            return rgba

        if len(old_value) == 4:
            rgba = [i for i in list(old_value)]

            return rgba

    # New Socket always will be CUSTOM when converting to Octane
    if new_socket.type == "CUSTOM":

        if hasattr(new_socket, "default_value"):
            new_default_value = new_socket.default_value

            # Handeling Int, Float Cases
            if isinstance(new_default_value, (float, int)):
                if isinstance(old_value, (float, int)):
                    return old_value

            # Handeling Color List Cases
            if len(new_default_value) == 3:
                if isinstance(old_value, (float, int)):
                    rgb = [i for i in colorsys.hsv_to_rgb(0.5, 0, old_value)]
                    return rgb

                if len(old_value) == 3:
                    rgb = [i for i in list(old_value)]

                    return rgb

                if len(old_value) == 4:
                    rgba = [i for i in list(old_value)]
                    return rgba[:-1]

    return old_value


def get_correct_custom_group_original_node_name(node_name, prefix):

    node_name = get_node_name_without_duplicate(node_name)

    if node_name.startswith(prefix):
        node_name = node_name.replace(
            prefix, "")

    return node_name


def get_node_name_without_duplicate(node_name):

    if len(node_name) >= 5:
        if node_name[-4] == "." and node_name[-3].isdigit() and node_name[-2].isdigit() and node_name[-1].isdigit():
            node_name = node_name[:-4]

    return node_name


def remove_reroute_node_from_node_tree(node_tree):

    for node in node_tree.nodes:

        if node.type == "GROUP":
            remove_reroute_node_from_node_tree(node.node_tree)

        if node.type == "REROUTE":
            remove_node_and_pass_link_through(node, 0, 0)
