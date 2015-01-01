#
#  Copyright (c) 2009-2014, Jack Poulson
#  All rights reserved.
#
#  This file is part of Elemental and is under the BSD 2-Clause License, 
#  which can be found in the LICENSE file in the root directory, or at 
#  http://opensource.org/licenses/BSD-2-Clause
#
import El
import time

m = 1000
n = 2000
testMehrotra = True
testIPF = True
#testADMM = False
display = False
worldRank = El.mpi.WorldRank()

# Make a sparse semidefinite matrix
def Semidefinite(height):
  Q = El.DistMatrix()
  El.Identity( Q, height, height )
  return Q

# Make a sparse matrix with the last column dense
def RectangDense(height,width):
  A = El.DistMatrix()
  El.Zeros( A, height, width )
  for s in xrange(height):
    A.Update( s, s, 11 )
    if s != 0:            A.Update( s, s-1,      1 )
    if s != width-1:      A.Update( s, s+1,      2 )
    if s >= height:       A.Update( s, s-height, 3 )
    if s <  width-height: A.Update( s, s+height, 4 )
    # The dense last column
    A.Update( s, width-1, 5./height );

  return A

Q = Semidefinite(n)
A = RectangDense(m,n)

# Generate a right-hand side in the positive image
# ================================================
xGen = El.DistMatrix()
El.Uniform(xGen,n,1,0.5,0.4999)
b = El.DistMatrix()
El.Zeros( b, m, 1 )
El.Gemv( El.NORMAL, 1., A, xGen, 0., b )

# Generate a random positive cost function
# ========================================
c = El.DistMatrix()
El.Uniform(c,n,1,0.5,0.4999)

if display:
  El.Display( A,    "A"    )
  El.Display( xGen, "xGen" )
  El.Display( b,    "b"    )
  El.Display( c,    "c"    )

# Generate random initial guesses
# ===============================
xOrig = El.DistMatrix()
yOrig = El.DistMatrix()
zOrig = El.DistMatrix()
El.Uniform(xOrig,n,1,0.5,0.4999)
El.Uniform(yOrig,m,1,0.5,0.4999)
El.Uniform(zOrig,n,1,0.5,0.4999)
x = El.DistMatrix()
y = El.DistMatrix()
z = El.DistMatrix()

if testMehrotra:
  El.Copy( xOrig, x )
  El.Copy( yOrig, y )
  El.Copy( zOrig, z )
  startMehrotra = time.clock()
  El.QPDirectMehrotra(Q,A,b,c,x,y,z)
  endMehrotra = time.clock()
  if worldRank == 0:
    print "Mehrotra time:", endMehrotra-startMehrotra

  if display:
    El.Display( x, "x Mehrotra" )
    El.Display( y, "y Mehrotra" )
    El.Display( z, "z Mehrotra" )

  Q_x = El.DistMatrix()
  El.Zeros( Q_x, n, 1 )
  El.Gemv( El.NORMAL, 1., Q, x, 0., Q_x )
  xTQx = El.Dot(x,Q_x)
  obj = El.Dot(c,x) + xTQx/2
  if worldRank == 0:
    print "Mehrotra primal objective =", obj

if testIPF:
  El.Copy( xOrig, x )
  El.Copy( yOrig, y )
  El.Copy( zOrig, z )
  startIPF = time.clock()
  El.QPDirectIPF(Q,A,b,c,x,y,z)
  endIPF = time.clock()
  if worldRank == 0:
    print "IPF time:", endIPF-startIPF

  if display:
    El.Display( x, "x IPF" )
    El.Display( y, "y IPF" )
    El.Display( z, "z IPF" )

  Q_x = El.DistMatrix()
  El.Zeros( Q_x, n, 1 )
  El.Gemv( El.NORMAL, 1., Q, x, 0., Q_x )
  xTQx = El.Dot(x,Q_x)
  obj = El.Dot(c,x) + xTQx/2
  if worldRank == 0:
    print "IPF primal objective =", obj

# TODO: Add ADMM test after implementation exists

# Require the user to press a button before the figures are closed
commSize = El.mpi.Size( El.mpi.COMM_WORLD() )
El.Finalize()
if commSize == 1:
  raw_input('Press Enter to exit')
