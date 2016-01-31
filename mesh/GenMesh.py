'''
GenMesh.py

Generate a 3D rectilinear mesh as node and element input files for LS-DYNA3D.

Copyright 2015 Mark L. Palmeri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
from __future__ import absolute_import
from __future__ import print_function
from six.moves import range

__author__ = "Mark Palmeri"
__email__ = "mlp6@duke.edu"
__license__ = "Apache v2.0"


def main():
    import sys
    import fem_mesh

    fem_mesh.check_version()

    # read in CLI arguments
    args = parse_cli()

    # generate node & element output files
    out_file_header = ("$ Generated using %s:\n$ %s\n$" %
                       (sys.argv[0], args))

    pos = calc_node_pos(args.xyz, args.numElem)

    # check to make sure nodes fall at (x, y) = (0, 0)
    check_x0_y0(pos)

    writeNodes(pos, args.nodefile, out_file_header)
    writeElems(args.numElem, args.partid, args.elefile, out_file_header)


def parse_cli():
    """parse commandline arguments

    Defines:
        --nodefile [nodes.dyn]
        --elefile [elems.dyn]
        --partid [1]
        --xyz [(xmin, xmax, ymin, ymax,...)]
        --numElem [(x, y, z)]
    """

    import argparse as ap

    par = ap.ArgumentParser(description="Generate rectilinear 3D mesh as "
                            "specified on the command line.",
                            formatter_class=ap.ArgumentDefaultsHelpFormatter)
    par.add_argument("--nodefile",
                     dest="nodefile",
                     help="node definition input file",
                     default="nodes.dyn")
    par.add_argument("--elefile",
                     dest="elefile",
                     help="element definition input file",
                     default="elems.dyn")
    par.add_argument("--partid",
                     dest="partid",
                     help="part ID to assign to the new structure",
                     type=int,
                     default=1)
    par.add_argument("--xyz",
                     dest="xyz",
                     help="x, y z ranges (xmin, xmax, ymin, ymax,...)",
                     type=float,
                     nargs='+',
                     default=(-1.0, 0.0, -1.0, 1.0, -4.0, 0.0))
    par.add_argument("--numElem",
                     dest="numElem",
                     help="number of elements (ints) in each dimension "
                          "(x, y, z)",
                     type=int,
                     nargs='+',
                     default=(20, 20, 20))

    args = par.parse_args()

    return args


def calc_node_pos(xyz, numElem):
    """Calculate nodal spatial positions based on CLI specs

    :param xyz: (xmin, xmax, ymin, ymax, zmin, zmax)
    :param int numElem: (xEle, yEle, zEle)
    :returns: pos - list of lists containing x, y, and z positions
    """
    import numpy as n
    import warnings as w
    import sys

    if len(xyz) != 6:
        sys.exit("ERROR: Wrong number of position range limits input.")

    pos = []
    for i, j in enumerate(range(0, 5, 2)):
        minpos = xyz[j]
        maxpos = xyz[j + 1]
        if maxpos < minpos:
            w.warn("Range values were swapped in order (max -> min) "
                   "and reversed.")
            minpos, maxpos = maxpos, minpos
        ptemp = n.linspace(minpos, maxpos, numElem[i] + 1)
        pos.append(ptemp.tolist())

    return pos


def writeNodes(pos, nodefile, header_comment):
    """write node file using calculated position data

    :param pos: list of lists of x, y, z positions
    :param nodefile: nodes.dyn
    :param header_comment: what version / syntax of calling command
    :returns: nodes.dyn written (or specified filename)
    """
    # TODO: clean up syntax
    nodesTotal = len(pos[0]) * len(pos[1]) * len(pos[2])

    NODEFILE = open(nodefile, 'w')
    NODEFILE.write("%s\n" % (header_comment))
    NODEFILE.write("*NODE\n")

    NodeID = 0
    for z in pos[2]:
        for y in pos[1]:
            for x in pos[0]:
                NodeID += 1
                NODEFILE.write("%i,%.6f,%.6f,%.6f\n" % (NodeID, x, y, z))
    NODEFILE.write("*END\n")
    NODEFILE.close()
    print(("%i/%i nodes written to %s" % (NodeID, nodesTotal, nodefile)))


def writeElems(numElem, partid, elefile, header_comment):
    """write element file using calculated position data

    :param pos: list of lists of x, y, z positions
    :param str elefile: elems.dyn
    :param str header_comment: what version / syntax of calling command
    :returns: elems.dyn written (or specified filename)
    """
    # calculate total number of expected elements
    elemTotal = numElem[0] * numElem[1] * numElem[2]

    ELEMFILE = open(elefile, 'w')
    ELEMFILE.write("%s\n" % (header_comment))
    ELEMFILE.write('*ELEMENT_SOLID\n')

    # defining the elements with outward normals w/ right-hand convention
    # assuming node ID ordering as was used to write the nodes.dyn file
    # (saves lots of RAM instead of saving that massive array)
    ElemID = 0
    yplane = 0
    zplane = 0
    for z in range(1, (numElem[2] + 1)):
        for y in range(1, (numElem[1] + 1)):
            for x in range(1, (numElem[0] + 1)):
                ElemID += 1
                n1 = (yplane + zplane) * (numElem[0] + 1) + x
                n2 = n1 + 1
                n4 = n1 + (numElem[0] + 1)
                n3 = n4 + 1
                n5 = (numElem[0] + 1) * (numElem[1] + 1) + n1
                n6 = n5 + 1
                n7 = n6 + (numElem[0] + 1)
                n8 = n7 - 1
                ELEMFILE.write("%i,%i,%i,%i,%i,%i,%i,%i,%i,%i\n" %
                               (ElemID,
                                partid,
                                n1,
                                n2,
                                n3,
                                n4,
                                n5,
                                n6,
                                n7,
                                n8))
            yplane += 1
        zplane += 1
    ELEMFILE.write("*END\n")
    ELEMFILE.close()
    print(("%i/%i elements written to %s" % (ElemID, elemTotal, elefile)))


def check_x0_y0(pos):
    """check model position
    Check to make sure that nodes exist at (x, y) = (0, 0) so that the focus /
    peak of an ARF excitation is captured by the mesh.

    :param pos: node positions
    :raises: warning if (0, 0) is not in the mesh
    :returns: 0/1 (1 = fail)
    """
    import warnings as w
    if 0.0 not in pos[0] and 0.0 not in pos[1]:
        w.warn("Your mesh does not contain nodes at (x, y) = (0, 0)!  This "
               "could lead to poor representation of your ARF focus.")
        return 1
    else:
        return 0


if __name__ == "__main__":
    main()
