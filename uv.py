import bpy
import bmesh
import mathutils
import math

from typing import List, Dict, Tuple

def str_loop(loop:bmesh.types.BMLoop) -> str:
    """more compact print of a bmloop"""
    return f"{loop.vert.index}/{loop.edge.index}/{loop.face.index}"


def is_same_uv_location(a:mathutils.Vector, b:mathutils.Vector) -> bool:
    '''to check if both loops have the same uv position'''
    return (a - b).length < 0.001


def link_loop_is_uv_connected(loop:bmesh.types.BMLoop, uv_layer:bmesh.types.BMLayerItem) -> bool:
    '''see if the uv edge is split'''
    a = loop
    b = loop.link_loop_radial_next
    use_same_locations = is_same_uv_location(
        a[uv_layer].uv, b.link_loop_next[uv_layer].uv
    ) and is_same_uv_location(b[uv_layer].uv, a.link_loop_next[uv_layer].uv)

    return use_same_locations


def get_uv_valence(loop:bmesh.types.BMLoop, uv_layer:bmesh.types.BMLayerItem) -> int:
    '''number of edges branching out from a uv vert'''
    uv = loop[uv_layer].uv

    valence = 0
    for loop in loop.vert.link_loops:
        if is_same_uv_location(uv, loop[uv_layer].uv):
            valence += 1

    return valence


def get_selected_uv_edge_loops(bm: bmesh.types.BMesh, uv_layer:bmesh.types.BMLayerItem) -> List[bmesh.types.BMLoop]:
    '''collect selected uv loops which have selected uv edges'''

    selected_uv_loops: List[bmesh.types.BMLoop] = []

    face: bmesh.types.BMFace
    for face in bm.faces:
        if not face.select:
            continue
       
        loop: bmesh.types.BMLoop
        for loop in face.loops: 
            if loop[uv_layer].select_edge:
                selected_uv_loops.append(loop)

    return selected_uv_loops


def get_selected_uv_vert_loops(bm:bmesh.types.BMesh, uv_layer:bmesh.types.BMLayerItem) -> List[bmesh.types.BMLoop]:
    '''collect selected uv loops - only checking the loop but not the edge'''

    selected_uv_loops: List[bmesh.types.BMLoop] = []

    face: bmesh.types.BMFace
    for face in bm.faces:
        if not face.select:
            continue

        loop: bmesh.types.BMLoop
        for loop in face.loops:
            if loop[uv_layer].select:
                selected_uv_loops.append(loop)

    return selected_uv_loops

def find_uv_edgerings(initial_uv_loops:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem, constrain_by_selected:bool=False) -> List[List[bmesh.types.BMLoop]]:
    '''returns list of sorted uv edgerings based on supplied initial uv loops'''

    edge_rings = []
    uv_loops = set(initial_uv_loops)

    while len(uv_loops) > 0:
        # print("-- new ring --")
        start = uv_loops.pop()
        edge_ring = [start]

        forward = True
        current = start
        cylic_ring = False
        # print(f"start: {str_loop(start)}")
        while True:
            next = find_uv_edgering_next(current, uv_layer, constrain_by_selected)
            current = None
            if next:
                # print(f"--- {str_loop(next)}")

                if forward:
                    edge_ring.append(next)
                else:
                    edge_ring.insert(0, next)

                if next in uv_loops:
                    uv_loops.remove(next)

                a = next
                b = next.link_loop_radial_next

                # on a cylinder end meets the start loop again, need to stop there
                if b == start.link_loop_radial_next or b == start:
                    cylic_ring = True

                if (
                    not cylic_ring
                    and link_loop_is_uv_connected(a, uv_layer)
                    and b.face.select
                ):
                    current = b
                    if current in uv_loops:
                        uv_loops.remove(current)

                    if forward:
                        edge_ring.append(current)
                    else:
                        edge_ring.insert(0, current)

            if cylic_ring:
                break

            # if no next loop is found - start looking reverse from the start loop
            if not current:
                if forward and not start.edge.is_boundary:
                    forward = False

                    if link_loop_is_uv_connected(start, uv_layer):
                        current = start.link_loop_radial_next
                        if current.face.select:
                            edge_ring.insert(0, current)
                            if current in uv_loops:
                                uv_loops.remove(current)
                    else:
                        break
                else:
                    break

        edge_rings.append(edge_ring)

    return edge_rings


def find_uv_edgering_next(a:bmesh.types.BMLoop, uv_layer:bmesh.types.BMLayerItem, constrain_by_selected:bool) -> Tuple(None, bmesh.types.BMLoop):
    '''returns the next loop from an uv edgering'''

    """
    . -----> .  ||  . --------> .
    ↑        |  ||  ↑           |
    a        b  ||  c           |
    |        |  ||  |           |
    |        ↓  ||  |           ↓
    . <----- .  ||  . <-------- .
    """

    # in a pure quad structure the next next edge is the other side of the quad
    b = a.link_loop_next.link_loop_next

    # so moving along the edges this must be the same as the start loop
    if b.link_loop_next.link_loop_next == a:
        if constrain_by_selected and not b[uv_layer].select_edge:
            return None

        return b
    else:
        return None


def expand_uv_edgering(uv_edgering:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem) -> None:
    '''expands the uv edgering by one uv edge'''

    first = uv_edgering[0]
    last = uv_edgering[-1]

    next = find_uv_edgering_next(last, uv_layer, False)
    prev = find_uv_edgering_next(first, uv_layer, False)

    if next:
        # print(f"next: {str_loop(next)}")
        uv_edgering.append(next)

    if prev:
        # print(f"prev: {str_loop(prev)}")
        uv_edgering.insert(0, prev)


def shrink_uv_edgering(uv_edgering:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem) -> None:
    '''shrinks the uv edgering by one edge'''

    if len(uv_edgering) < 2:
        return

    a = uv_edgering.pop(0)
    a[uv_layer].select_edge = False
    a[uv_layer].select = False

    if uv_edgering[0].link_loop_radial_next == a:
        a = uv_edgering.pop(0)
        a[uv_layer].select_edge = False
        a[uv_layer].select = False

    if len(uv_edgering) < 2:
        return

    b = uv_edgering.pop(-1)
    b[uv_layer].select_edge = False
    b[uv_layer].select = False

    if uv_edgering[-1].link_loop_radial_next == b:
        b = uv_edgering.pop(-1)
        b[uv_layer].select_edge = False
        b[uv_layer].select = False


def select_uv_edgering(uv_edgering:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem) -> None:
    '''selects the uv edgering'''

    for loop in uv_edgering:
        loop_uv = loop[uv_layer]
        loop_uv.select_edge = True

        loop_next = loop.link_loop_next
        loop_next_uv = loop_next[uv_layer]

        for connected in loop.vert.link_loops:
            if not connected.face.select:
                continue
            
            connected_uv = connected[uv_layer]
            if is_same_uv_location(connected_uv.uv, loop_uv.uv):
                connected_uv.select = True

        for connected in loop_next.vert.link_loops:
            if not connected.face.select:
                continue

            connected_uv = connected[uv_layer]
            if is_same_uv_location(connected_uv.uv, loop_next_uv.uv):
                connected_uv.select = True


def find_uv_edgeloop_next(start_loop, uv_layer:bmesh.types.BMLayerItem, constrain_by_selected:bool) -> Tuple(None, bmesh.types.BMLoop):
    '''searches the next loop of a uv edgeloop'''

    """
    reminder for variable names...

    ABCDE -> vertices
    abcde, mnopq -> loops

    C has split uv's -> p,d

    ← e ← . C1   C   C2. → q →
            ↘    |   ↗
            d ↘  | ↗ p
       . ← c ← . | . ←  o ← .
       D --------B---------- E
       . → b → . | . → n  → .
               | | ↑
         PREV  a | m  NEXT
               ↓ | |
         ← f ← . A .  ←  r  ←

    """

    # print("next current: ", str_loop(start_loop))

    m = start_loop
    n = m.link_loop_next
    o = n.link_loop_radial_next
    p = o.link_loop_next
    q = p.link_loop_next
    d = p.link_loop_radial_next
    c = d.link_loop_next
    a = m.link_loop_radial_next
    f = a.link_loop_next

    # print(f"  n: {str_loop(n)}, o: {str_loop(o)}, p: {str_loop(p)}")

    if constrain_by_selected and not p[uv_layer].select_edge:
        # print(" not selected ")
        return None

    if is_same_uv_location(m[uv_layer].uv, f[uv_layer].uv) != is_same_uv_location(
        n[uv_layer].uv, a[uv_layer].uv
    ):
        # print(f" m: {str_loop(m)}, f: {str_loop(f)} | n: {str_loop(n)}, a: {str_loop(a)}")
        # print( is_same_uv_location(m[uv_layer].uv, f[uv_layer].uv), is_same_uv_location(n[uv_layer].uv, a[uv_layer].uv))
        # print(" start verts uvs not in same state location - either both connected / split")
        return None

    if n.edge.is_boundary:
        # print(" boundary - toplogical border")
        return None

    if not p.face.select:
        return None

    if get_uv_valence(n, uv_layer) != 4 and link_loop_is_uv_connected(p, uv_layer):
        return None

    if not is_same_uv_location(n[uv_layer].uv, p[uv_layer].uv):
        # print(" connected vert uvs not same location")
        return None

    if is_same_uv_location(d[uv_layer].uv, q[uv_layer].uv) != is_same_uv_location(
        p[uv_layer].uv, c[uv_layer].uv
    ):
        # print(f" d: {str_loop(d)}, q: {str_loop(q)} | p: {str_loop(p)}, c: {str_loop(c)}")
        # print( is_same_uv_location(d[uv_layer].uv, q[uv_layer].uv), is_same_uv_location(p[uv_layer].uv, c[uv_layer].uv))
        # print(" other side vert uvs not same location")
        return None

    return p


def find_uv_edgeloop_prev(start_loop:bmesh.types.BMLoop, uv_layer:bmesh.types.BMLayerItem, constrain_by_selected:bool) -> Tuple(None, bmesh.types.BMLoop):
    '''searches the previous loop of a uv edgeloop'''

    # print("prev current: ", str_loop(start_loop))

    a = start_loop
    b = start_loop.link_loop_prev
    c = b.link_loop_radial_next
    d = c.link_loop_prev
    f = a.link_loop_next
    m = a.link_loop_radial_next
    n = m.link_loop_next
    o = n.link_loop_radial_next
    p = d.link_loop_radial_next
    q = p.link_loop_next

    # print(f"  a: {str_#loop(a)}, b: {str_loop(b)}, c: {str_loop(c)}")

    if constrain_by_selected and not d[uv_layer].select_edge:
        # print(" not selected ")
        return None

    if is_same_uv_location(m[uv_layer].uv, f[uv_layer].uv) != is_same_uv_location(
        n[uv_layer].uv, a[uv_layer].uv
    ):
        # print(f" m: {str_loop(m)}, f: {str_loop(f)} | n: {str_loop(n)}, a: {str_loop(a)}")
        # print( is_same_uv_location(m[uv_layer].uv, f[uv_layer].uv), is_same_uv_location(n[uv_layer].uv, a[uv_layer].uv))
        # print(" start verts uvs not in same state location - either both connected / split")
        return None

    if b.edge.is_boundary:
        # print(" boundary - toplogical border")
        return None

    if not d.face.select:
        return None

    # print(f"valence: {get_uv_valence(a, uv_layer)}")
    if get_uv_valence(n, uv_layer) != 4 and link_loop_is_uv_connected(d, uv_layer):
        return None

    if not is_same_uv_location(a[uv_layer].uv, c[uv_layer].uv):
        # print(" connected vert uvs not same location")
        return None

    if is_same_uv_location(d[uv_layer].uv, q[uv_layer].uv) != is_same_uv_location(
        p[uv_layer].uv, c[uv_layer].uv
    ):
        # print(f" d: {str_loop(d)}, q: {str_loop(q)} | p: {str_loop(p)}, c: {str_loop(c)}")
        # print( is_same_uv_location(d[uv_layer].uv, q[uv_layer].uv), is_same_uv_location(p[uv_layer].uv, c[uv_layer].uv))
        # print(" other side vert uvs not same location")
        return None

    return d


def find_uv_edgeloops(initial_uv_loops:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem, constrain_by_selected:bool = False) -> List[List[bmesh.types.BMLoop]]:
    '''returns a list of sorted uv edgeloops searched from the intial uv loops'''

    edgeloops = []
    uv_loops = set(initial_uv_loops)

    while len(uv_loops) > 0:
        start_loop = uv_loops.pop()
        edge_loop = [start_loop]

        # print("forward:")
        current = start_loop
        while True:
            next_loop = find_uv_edgeloop_next(current, uv_layer, constrain_by_selected)
            if next_loop and next_loop != start_loop:
                if next_loop in uv_loops:
                    uv_loops.remove(next_loop)

                # print(f" add: {str_loop(next_loop)} - loops left: {len(uv_loops)}" )
                edge_loop.append(next_loop)
                current = next_loop
            else:
                break

        # print("reverse:")
        current = start_loop
        while True:
            prev_loop = find_uv_edgeloop_prev(current, uv_layer, constrain_by_selected)
            if prev_loop and prev_loop != start_loop:
                if prev_loop in uv_loops:
                    uv_loops.remove(prev_loop)

                # print(f" add: {str_loop(prev_loop)} - loops left: {len(uv_loops)}" )
                edge_loop.insert(0, prev_loop)
                current = prev_loop
            else:
                break

        edgeloops.append(edge_loop)

    return edgeloops


def expand_uv_edgeloop(uv_edgeloop:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem) -> None:
    '''expands the uv edgeloop by the next uv edge on both ends'''

    next_loop = find_uv_edgeloop_next(uv_edgeloop[-1], uv_layer, False)
    prev_loop = find_uv_edgeloop_prev(uv_edgeloop[0], uv_layer, False)

    if next_loop:
        # print(f"add next: {str_loop(next_loop)}")
        uv_edgeloop.append(next_loop)

    if prev_loop:
        # print(f"add prev: {str_loop(prev_loop)}")
        uv_edgeloop.insert(0, prev_loop)


def shrink_uv_edgeloop(uv_edgeloop:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem) -> None:
    '''shrinks the uv edgeloop by the next uv edge on both ends'''

    if len(uv_edgeloop) > 1:
        a = uv_edgeloop.pop(0)
        a[uv_layer].select_edge = False
        a[uv_layer].select = False

        b = uv_edgeloop.pop(-1)
        b[uv_layer].select_edge = False
        b[uv_layer].select = False


def select_uv_edgeloop(uv_edgeloop:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem) -> None:
    '''selects the uv edgeloop'''

    for loop in uv_edgeloop:
        loop[uv_layer].select_edge = True

        loop_uv = loop[uv_layer]
        loop_uv.select = True

        for connected in loop.vert.link_loops:
            if not connected.face.select:
                continue

            connected_uv = connected[uv_layer]
            if is_same_uv_location(connected_uv.uv, loop_uv.uv):
                connected_uv.select = True


def find_uv_islands_for_selected_uv_loops(intial_loops:List[bmesh.types.BMLoop], uv_layer:bmesh.types.BMLayerItem) -> List[List[bmesh.types.BMLoop]]:
    '''returns a list of uv islands which are searched from the initial loops - uv islands are unordered lists of uv loops'''

    islands = []
    search_loops = set(intial_loops)
    while len(search_loops) > 0:
        seed = search_loops.pop()

        already_searched = set()
        already_searched.add(seed.index)

        island = []
        island.append(seed)
        candindates = [seed]

        while len(candindates) > 0:
            current = candindates.pop()

            for face_connected in current.face.loops:
                if not face_connected.face.select:
                    continue

                if face_connected.index in already_searched:
                    continue
                already_searched.add(face_connected.index)

                island.append(face_connected)

                if face_connected in search_loops:
                    search_loops.remove(face_connected)

                if link_loop_is_uv_connected(face_connected, uv_layer):
                    for (
                        other_face_connected
                    ) in face_connected.link_loop_radial_next.face.loops:
                        if not other_face_connected.face.select:
                            continue

                        if other_face_connected.index not in already_searched:
                            candindates.append(other_face_connected)

        islands.append(island)
    return islands
