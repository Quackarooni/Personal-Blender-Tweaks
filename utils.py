import bpy
import itertools
from functools import wraps

from bpy.types import Node, NodeSocketVirtual


weird_offset = 10
reroute_width = 10

default_dimensions = {"NodeFrame": (150, 100)}


class TemporaryUnframe:
    def __init__(self, nodes):
        self.parent_dict = {}
        for node in nodes:
            if node.parent is not None:
                self.parent_dict[node] = node.parent
            node.parent = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for node, parent in self.parent_dict.items():
            node.parent = parent


def extend_to_return_tuple(func):
    @wraps(func)
    def wrapper(*args, as_tuple=False, **kwargs):
        result = func(*args, **kwargs)
        if as_tuple:
            result = tuple(result)

        return result

    return wrapper


def transfer_properties(source, target, props):
    for prop_name in props:
        prop = getattr(source, prop_name)
        setattr(target, prop_name, prop)


def fetch_user_preferences(attr_id=None):
    prefs = bpy.context.preferences.addons[__package__].preferences

    if attr_id is None:
        return prefs
    else:
        return getattr(prefs, attr_id)


def get_width(node):
    if node.bl_idname == "NodeReroute":
        return reroute_width
    else:
        return node.width


def group_input_dimensions(node):
    visible_outputs = tuple(
        soc
        for soc in node.outputs
        if not (soc.hide or isinstance(soc, NodeSocketVirtual))
    )
    height = 50 + (22 * len(visible_outputs))

    return node.width, height


def get_height(node):
    ##return node.width * node.dimensions.y / node.dimensions.x
    dim_x, dim_y = node.dimensions
    if (dim_x == 0) and (dim_y == 0):
        if node.bl_idname == "NodeGroupInput":
            dimensions = group_input_dimensions(node)
        else:
            dimensions = default_dimensions.get(node.bl_idname)

        if dimensions is None:
            raise ValueError(f"Could not retrieve dimensions of node - {node}")
        dim_x, dim_y = dimensions

    return get_width(node) * dim_y / dim_x


def get_left(node):
    if node.bl_static_type == "REROUTE":
        return node.location.x
    else:
        return node.location.x


def get_center(node):
    if node.bl_static_type == "REROUTE":
        return node.location.x
    else:
        return node.location.x + (0.5 * node.width)


def get_right(node):
    if node.bl_static_type == "REROUTE":
        return node.location.x
    else:
        return node.location.x + node.width


def get_top(node):
    if node.bl_static_type == "REROUTE":
        return node.location.y
    elif node.hide:
        return node.location.y + (0.5 * get_height(node)) - weird_offset
    else:
        return node.location.y


def get_middle(node):
    if node.bl_static_type == "REROUTE":
        return node.location.y
    elif node.hide:
        return node.location.y - weird_offset
    else:
        return node.location.y - (0.5 * get_height(node))


def get_bottom(node):
    if node.bl_static_type == "REROUTE":
        return node.location.y
    elif node.hide:
        return node.location.y - (0.5 * get_height(node)) - weird_offset
    else:
        return node.location.y - get_height(node)


def get_bounds(nodes):
    if len(nodes) <= 0:
        return 0, 0, 0, 0

    min_x = min(get_left(node) for node in nodes)
    max_x = max(get_right(node) for node in nodes)
    min_y = min(get_bottom(node) for node in nodes)
    max_y = max(get_top(node) for node in nodes)

    return min_x, max_x, min_y, max_y


def get_bounds_midpoint(nodes):
    nodes = tuple(n for n in nodes if n.bl_idname != "NodeFrame")

    min_x, max_x, min_y, max_y = get_bounds(nodes)
    midpoint_x = 0.5 * (min_x + max_x)
    midpoint_y = 0.5 * (min_y + max_y)

    return midpoint_x, midpoint_y


@extend_to_return_tuple
def filter_hidden_links(links):
    for link in links:
        if link.is_hidden:
            yield link


@extend_to_return_tuple
def filter_hidden_data_blocks(links):
    for link in links:
        try:
            socket = link.to_socket
            data_block = socket.default_value
            getattr(data_block, "name")

            yield (link, socket, data_block)

        except AttributeError:
            pass


@extend_to_return_tuple
def get_data_block_defaults(tree, *, in_out):
    for socket in tree.interface.items_tree:
        if socket.item_type == 'PANEL':
            continue
        
        # in_out_status = True if (in_out == 'BOTH') else socket.in_out == in_out
        # TODO - Add enums for selecting ('INPUT', 'OUTPUT', 'BOTH') and erroring at invalid inputs
        in_out_status = True if (in_out == "BOTH") else socket.in_out == in_out

        if in_out_status:
            if not hasattr(socket, "default_value"):
                continue

            data_block = socket.default_value

            if hasattr(data_block, "name"):
                yield socket, data_block


def fetch_active_nodetree(context):
    edit_tree = context.space_data.edit_tree
    node_tree = context.space_data.node_tree

    if edit_tree is not None:
        return edit_tree
    else:
        return node_tree


def transfer_node_links(tree, source, destination):
    for link in source.links:
        if source.is_output:
            link_start = destination
            link_end = link.to_socket
        else:
            link_start = link.from_socket
            link_end = destination

        tree.links.new(link_start, link_end)


def arrange_along_column(nodes, spacing):
    def spacing_func(a, b):
        return a - (get_height(b) + spacing)

    first_node = next(iter(nodes))
    positions = itertools.accumulate(
        nodes, func=spacing_func, initial=get_height(first_node)
    )

    for node, pos in zip(nodes, positions):
        node.location.y = pos


def align_by_bounding_box(target_nodes, nodes_to_move):
    if isinstance(target_nodes, Node):
        target_nodes = (target_nodes,)
    if isinstance(nodes_to_move, Node):
        nodes_to_move = (nodes_to_move,)

    target = get_bounds(target_nodes)
    current_pos = get_bounds(nodes_to_move)

    offset_x = 0.5 * (target[0] + target[1]) - 0.5 * (current_pos[0] + current_pos[1])
    offset_y = 0.5 * (target[2] + target[3]) - 0.5 * (current_pos[2] + current_pos[3])

    for node in nodes_to_move:
        node.location.x += offset_x
        node.location.y += offset_y
