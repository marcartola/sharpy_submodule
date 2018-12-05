'''
Collect tools to manipulate sparse and/or mixed dense/sparse matrices.

author: S. Maraniello
date: Dec 2018 

Comment: manipulating large linear system may require using both dense and sparse
matrices. While numpy/scipy automatically handle most operations between mixed
dense/sparse arrays, some (e.g. dot product) require more attention. This 
library collects methods to handle these situations.

Classes:
scipy.sparse matrices are wrapped so as to ensure compatibility with numpy arrays
upon conversion to dense.
- csc_matrix: this is a wrapper of scipy.csc_matrix.

Methods:
- dot: handles matrix dot products across different types.
- solve: solves linear systems Ax=b with A and b dense, sparse or mixed.
- dense: convert matrix to numpy array

Warning: 
- only sparse types into SupportedTypes are supported!

To Do: 
- move these methods into an algebra module?
'''

import warnings
import numpy as np
import scipy.sparse as sparse
import scipy.sparse.linalg as spalg



# --------------------------------------------------------------------- Classes

class csc_matrix(sparse.csc_matrix):
	'''
	Wrapper of scipy.csc_matrix where the following methods has been 
	overwritten to ensure best compatibility with numpy dense arrays.
	- todense: 
		returns numpy.ndarray intstead of numpy.matrixlib.defmatrix.matrix
	'''

	def __init__(self,arg1, shape=None, dtype=None, copy=False):
		super().__init__(arg1, shape=shape, dtype=dtype, copy=copy)

	def todense(self):
		''' As per scipy.spmatrix.todense but returns a numpy.ndarray. '''
		return np.array(super().todense())



# --------------------------------------------------------------------- Methods

SupportedTypes=[np.ndarray, csc_matrix]


def dot(A,B,type_out=None):
	'''
	Method to compute
		C = A*B ,
	where * is the matrix product, with dense/sparse/mixed matrices.

	The format (sparse or dense) of C is specified through 'type_out'. If
	type_out==None, the output format is sparse if both A and B are sparse, dense
	otherwise.

	The following formats are supported:
	- numpy.ndarray
	- scipy.csc_matrix
	'''

	# determine types:
	tA=type(A)
	tB=type(B)

	assert tA in SupportedTypes, 'Type of A matrix (%s) not supported'%tA
	assert tB in SupportedTypes, 'Type of B matrix (%s) not supported'%tB
	if type_out == None:
		type_out=tA
	else:
		assert type_out in SupportedTypes, 'type_out not supported'		

	# multiply
	if tA==np.ndarray and tB==csc_matrix:
		C=(B.transpose()).dot(A.transpose()).transpose()
	else:
		C=A.dot(B)

	# format output 
	if tA != type_out:
		if type_out==csc_matrix:
			return csc_matrix(C)
		else:
			return C.todense()
	return C


def solve(A,b):
	'''
	Wrapper of 
		numpy.linalg.solve and scipy.sparse.linalg.spsolve 
	for solution of the linear system A x = b.
	- if A is a dense numpy array np.linalg.solve is called for solution. Note 
	that if B is sparse, this requires convertion to dense. In this case, 
	solution through LU factorisation of A should be considered to exploit the
	sparsity of B.
	- if A is sparse, scipy.sparse.linalg.spsolve is used.
	'''

	# determine types:
	tA=type(A)
	tB=type(b)

	assert tA in SupportedTypes, 'Type of A matrix (%s) not supported'%tA
	assert tB in SupportedTypes, 'Type of B matrix (%s) not supported'%tB
	# multiply
	if tA==np.ndarray:
		if tB==csc_matrix:
			x=np.linalg.solve(A,b.todense())
		else:
			x=np.linalg.solve(A,b)
	else:
		x=spalg.spsolve(A,b)

	assert type(x) in SupportedTypes, 'Unexpected output type!'

	return x


def dense(M):
	''' If required, converts sparse array to dense. '''
	if type(M) == csc_matrix:
		return np.array(M.todense())
	elif type(M) == csc_matrix:
		return M.todense()
	return M


def eye_as(M):
	''' Produces an identity matrix as per M '''

	tM=type(M)
	assert tM in SupportedTypes, 'Type %s not supported!'%tM
	nrows=M.shape[0]
	assert nrows==M.shape[1], 'Not a square matrix!'

	if tM==csc_matrix:
		D=csc_matrix((nrows,nrows))
		D.setdiag(1.)
	elif tM==np.ndarray:
		D=np.eye(nrows)

	return D


if __name__=='__main__':
	import unittest


	class Test_module(unittest.TestCase):
		''' Test methods into this module '''


		def setUp(self):
			self.A=np.random.rand(3,4)
			self.B=np.random.rand(4,2)

		def test_csc_matrix_class(self):
			A=self.A
			Asp=csc_matrix(A)
			assert type(A+Asp)==np.ndarray, 'Unexpected type with sum operator'

		def test_eye_as(self):
			A=np.random.rand(4,4)
			D0=np.eye(4)
			D1=eye_as(A)
			D2=eye_as(csc_matrix(A))
			assert np.max(np.abs(D0-D1))<1e-12, 'Error in libsparse.eye_as'
			assert np.max(np.abs(D0-D2))<1e-12, 'Error in libsparse.eye_as'

		def test_dot(self):
			A,B=self.A,self.B
			C0=np.dot(A,B)		# reference
			C1=dot(A,B)
			C2=dot(A,csc_matrix(B))
			C3=dot(csc_matrix(A),B)
			C4=dot(csc_matrix(A),csc_matrix(B))
			assert np.max(np.abs(C0-C1))<1e-12, 'Error in libsparse.dot'
			assert np.max(np.abs(C0-C2))<1e-12, 'Error in libsparse.dot'
			assert np.max(np.abs(C0-C3))<1e-12, 'Error in libsparse.dot'

		def test_solve(self):
			A=np.random.rand(4,4)
			B=np.random.rand(4,2)
			Asp=csc_matrix(A)
			Bsp=csc_matrix(B)

			X0=np.linalg.solve(A,B)
			X1=solve(A,B)
			X2=solve(A,Bsp)
			X3=solve(Asp,B)
			X4=solve(Asp,Bsp)			

			assert np.max(np.abs(X0-X1))<1e-12, 'Error in libsparse.solve'
			assert np.max(np.abs(X0-X2))<1e-12, 'Error in libsparse.solve'
			assert np.max(np.abs(X0-X3))<1e-12, 'Error in libsparse.solve'
			assert np.max(np.abs(X0-X4))<1e-12, 'Error in libsparse.solve'


	outprint='Testing libsparse'
	print('\n' + 70*'-')
	print((70-len(outprint))*' ' + outprint )
	print(70*'-')
	unittest.main()




