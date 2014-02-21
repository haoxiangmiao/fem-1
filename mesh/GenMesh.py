'''
GenMesh.py

Generate a 3D rectilinear mesh as node and element input files for LS-DYNA3D.

LICENSE:
The MIT License (MIT)

Copyright (c) 2014 Mark L. Palmeri

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

__author__ = "Mark Palmeri"
__email__ = "mlp6@duke.edu"
__created = "2013-08-21"
__modified__ = "2014-02-21"
__version__ = __modified__
__license__ = "MIT"


def main():
    import sys
    import fem_mesh

    fem_mesh.check_version()

    # read in CLI arguments
    args = parse_cli()

    # generate node & element output files
    out_file_header = ("$ Generated using %s (v%s):\n$ %s\n$" %
                       (sys.argv[0], __version__, args))

    pos = calc_node_pos(args.n1, args.n2, args.numElem)

    writeNodes(pos, args.nodefile, out_file_header)
    writeElems(args.numElem, args.partid, args.elefile, out_file_header)


def parse_cli():
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
                     default=1)
    par.add_argument("--n1",
                     dest="n1",
                     help="first mesh vertex (x, y, z)",
                     default=(-1, -1, 0))
    par.add_argument("--n2",
                     dest="n2",
                     help="second mesh vertex (x, y, z)",
                     default=(1, 1, 2))
    par.add_argument("--numElem",
                     dest="numElem",
                     help="number of elements (ints) in each dimension "
                          "(x, y, z)",
                     default=(20, 20, 20))

    args = par.parse_args()

    return args


def calc_node_pos(n1, n2, numElem):
    """
    Calculate nodal spatial positions based on CLI specs
    INPUTS
        n1 (x1, y1, z1) - tuple
        n2 (x2, y2, z2) - tuple
        numElem (xEle, yEle, zEle) - int tuple

    OUTPUT
        pos - list of lists containing x, y, and z positions
    """
    import numpy as n

    pos = []
    for i in range(0, 3):
        pos_range = [n1[i], n2[i]]
        a = min(pos_range)
        b = max(pos_range)
        ptemp = n.linspace(a, b, numElem[i] + 1)
        pos.append(ptemp.tolist())

    return pos


def writeNodes(pos, nodefile, header_comment):
    """
    write node file using calculated position data

    INPUTS
        pos - list of lists of x, y, z positions
        nodefile - nodes.dyn
        header_comment - what version / syntax of calling command

    OUTPUTS
        nodes.dyn written (or specified filename)
    """
    nodesTotal = pos[0].__len__() * pos[1].__len__() * pos[2].__len__()

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
    print("%i/%i nodes written to %s" % (NodeID, nodesTotal, nodefile))

    # test to make sure the correct number of nodes were generated
    try:
        NodeID = nodesTotal
    except ValueError:
        print("An incorrect number of nodes were generated.")


def writeElems(numElem, partid, elefile, header_comment):
    """
    write element file using calculated position data

    INPUTS
        pos - list of lists of x, y, z positions
        elefile - elems.dyn
        header_comment - what version / syntax of calling command

    OUTPUTS
        elems.dyn written (or specified filename)
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
            for x in range(1, (numElem[1] + 1)):
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
    print("%i/%i elements written to %s" % (ElemID, elemTotal, elefile))

    # test to make sure the correct number of elements were generated
    try:
        ElemID = elemTotal
    except ValueError:
        print("An incorrect number of elements were generated.")

if __name__ == "__main__":
    main()
