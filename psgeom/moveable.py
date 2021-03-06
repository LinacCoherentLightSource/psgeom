
"""
move.py
"""


import abc
import six
import numpy as np


@six.add_metaclass(abc.ABCMeta)
class MoveableParent:
    """
    A specific class can be a parent.
    """
    
    @property
    def num_children(self):
        return len(self._children)
    
        
    @property
    def children(self):
        return self._children

        
    def add_child(self, child):
    
        # if not (isinstance(child, CompoundCamera) or \
        #         isinstance(child, sensors.SensorElement)):
        #         raise TypeError('`child` must be type: SensorElement or '
        #                         'CompoundCamera')
    
        for c in self.children:
            if c.name == child.name:
                if c is child:
                    raise NameError('Child object already registered with parent!')
                else:
                    raise NameError('Child with name %s already registered with'
                                    ' this parent (%s) -- please change the ID'
                                    ' number to give this object a unique name '
                                    'and re-register it as a child object' % \
                                    (child.name, self.name))
    
        self.children.append(child)
        child._parent = self
    
        return
        
        
    def remove_child(self, child):
        self.children.remove(child)
        child._parent = None
        return
            
    
    @property
    def leaves(self):
        
        leaves = []
        
        def add_leaves(node):
            for c in node.children:
                if hasattr(c, 'children'):
                    add_leaves(c)
                else:
                    leaves.append(c)
                    
        add_leaves(self)
                    
        return leaves
        
        
    def draw_tree(self):
        """
        Sketch the camera tree, with this node as the root (higher levels in
        the heirarchy will not be shown)
        """

        print("--- " + str(self.name))
        
        def draw_child_tree(current, depth):
        
            for c in current.children:
                print(depth * "    " + "|-- " + str(c.name))
                if hasattr(c, 'children'):
                    draw_child_tree(c, depth + 1)
                    
        draw_child_tree(self, 1)
        
        return
        
        
    def _sort_tree(self):
        """
        Order the tree by the id_num of each tree node.
        """
        
        self._children = sorted(self._children, key=lambda x : x.id_num)
        for c in self.children:
            if hasattr(c, '_sort_tree'):
                c._sort_tree()
        
        return
    
    

@six.add_metaclass(abc.ABCMeta)
class MoveableObject:
    """
    An abstract base class for moveable objects.
    """
    
    
    @property
    def rotation_angles(self):
        return np.array(self._rotation_angles)
        
        
    @property
    def translation(self):
        return np.array(self._translation)
        
        
    @property
    def parent(self):
        return self._parent
        
        
    @property
    def type_name(self):
        return self._type_name
        
    
    @property
    def id(self):
        return self._id
        
    
    @property
    def name(self):
        return '%s-%d' % (self.type_name, self.id)
        
        
    def set_parent(self, parent):
        """
        Set the parent of the current object to `parent` and add the current
        instance to the list of `parent`s children.
        
        Parameters
        ----------
        parent : CompoundDetector
            The parent CompoundDetector object
        """
        
        # TJL to self: should CompoundDetector be some placeholder class here?
        if parent is not None:
            if not isinstance(parent, MoveableParent):
                raise TypeError('parents of MoveableObject (%s) may only be of type '
                                'MoveableParent. Got: %s' % (self.name, type(parent)))
            else:
                if hasattr(self, '_parent'):
                    if self._parent is not None:
                        self._parent.remove_child(self) # remove from old parent
                parent.add_child(self)    # add to new parent
                self._parent = parent
        else:
            self._parent = None # this is OK too
        
        return
    
    
    def rotate(self, alpha, beta, gamma):
        self._rotation_angles += np.array([alpha, beta, gamma])
        return
        
        
    def translate(self, translation):
        self._translation += translation
        return
    
        
    @property
    def local_transform(self):
        """
        Compute and return the local transfomation of this node with respect
        to the parent frame.
        
        Returns
        -------
        transform : np.ndarray
            A 4x4 matrix representing a rotation and translation
        """
        
        R0 = _rotation_matrix_from_angles(*self.rotation_angles,
                                          dummy_dimension=True)
        T0 = _translation_matrix_from_vector(self.translation)
        
        return np.dot(T0, R0)
    
        
    @property
    def global_transform(self):
        """
        Compute and return the global transfomation of this node with respect
        to the absolute coordinate system.
        
        Returns
        -------
        transform : np.ndarray
            A 4x4 matrix representing a rotation and translation
        """
        
        T = self.local_transform
        if self.parent:
            P = self.parent.global_transform
            T = np.dot(P, T)
        
        return T
    
        
    @staticmethod
    def _evaluate_transform(transform, xyz):
        """
        Evaluate the effect of a 4x4 tranform matrix on an array of
        vectors, called `xyz`.
        
        Parameters
        ----------
        xyz : np.ndarray
            An (N, ..., 3)-shape array of vectors (last dim must be size 3)
            
        Returns
        -------
        Txyz : np.ndarray
            An (N, ..., 3)-shape array of vectors transformed by `transform`
        """
        
        if not xyz.shape[-1] == 3:
            raise ValueError('last dimenson of `xyz` must be size 3 '
                             '(cartensian), got shape: %s' % str(xyz.shape))
        if not transform.shape == (4,4):
            raise ValueError('transform must be 4x4 matrix, got shape:'
                             '%s' % str(transform.shape))
        
        # augment xyz with an additional row of 1's (dummy dimension)
        # necessary for matrix representation of translations
        buff = np.ones( list(xyz.shape[:-1]) + [1], dtype=xyz.dtype)
        xyzd = np.concatenate([xyz, buff], axis=-1)
        
        # do the transformation
        Txyzd = np.dot(xyzd, transform.T) # recall: (A.B^T)^T = B.A^T
        assert Txyzd.shape[-1] == 4
        
        # remove dummy dimension
        Txyz = Txyzd[...,:3]
        assert Txyz.shape == xyz.shape, 'output shape not same as input shape'
        
        return Txyz


def _translation_matrix_from_vector(v):
    """
    Compute a translation matrix T for vector v. If x is a 3-vector, then

        dot(T, y)[:3] = x + v

    where y is a 4-vector with an appended one: y[0:3] = x, y[3] = 1.

    Parameters
    ----------
    v : np.ndarray
        3-vector of a translation

    Returns
    -------
    T : np.ndarray
        A 4x4 translation matrix

    Citation
    --------
    ..[1] http://en.wikipedia.org/wiki/Translation_%28geometry%29#Matrix_
          representation
    """

    T = np.zeros((4,4), dtype=np.float64)
    di = np.diag_indices(4)

    T[di]    = 1.0
    T[0:3,3] = v.copy()

    return T


def _rotation_matrix_from_angles(gamma, beta, alpha, dummy_dimension=False,
                                 angle_units='degrees'):
    """
    Compute a rotation matrix from a triple of Cardan angles. Note that the
    Cardan angles are Euler-like with a z-y'-x'' (intrinsic rotation) 
    convention.

    Parameters
    ----------
    gamma/beta/alpha : float
        The 3 Cardan angles to construct the rotation from. They represent
        rotations around the z/y/x axes, respectively, where the axis system
        rotates (intrinsic rotation) in the order z-y-x. Default units 
        degrees, see `angle_units`.
        
    dummy_dimension : bool
        If `True`, add a 4th dimenson that is not rotated. Useful for
        composition with translation matrices.
        
    angle_units : 
    
    Returns
    -------
    R : np.ndarray
        A 3x3 rotation matrix
        
    References
    ----------
    ..[1] https://en.wikipedia.org/wiki/Euler_angles
    ..[2] https://confluence.slac.stanford.edu/display/PSDM/Detector+Geometry
    """
    
    if angle_units == 'degrees':
        alpha = np.radians(alpha)
        beta  = np.radians(beta)
        gamma = -np.radians(gamma)
    elif angle_units == 'radians':
        pass
    else:
        raise ValueError('arg `angle_units` must be "degrees" or "radians"')
        

    Rx = np.array([[            1.0,            0.0,            0.0],
                   [            0.0,  np.cos(alpha), -np.sin(alpha)],
                   [            0.0,  np.sin(alpha),  np.cos(alpha)]
                   ])
    Ry = np.array([[   np.cos(beta),            0.0,  -np.sin(beta)],
                   [            0.0,            1.0,            0.0],
                   [   np.sin(beta),            0.0,   np.cos(beta)]
                   ])
    Rz = np.array([[  np.cos(gamma),  np.sin(gamma),            0.0],
                   [ -np.sin(gamma),  np.cos(gamma),            0.0],
                   [            0.0,            0.0,            1.0]
                   ])

    R = np.dot(Rx, np.dot(Ry, Rz))
    assert R.shape == (3,3)

    if dummy_dimension:
        Rp = np.zeros((4,4), dtype=R.dtype)
        Rp[:3,:3] = R
        Rp[3,3]   = 1.0
        R = Rp

    return R



def _angles_from_rotated_frame(xp, yp, zp, return_units='degrees',
                               orthog_tol=1e-2, cardan_tol=1e-5):
    """
    Compute the Cardan angles alpha/beta/gamma from a rotated frame.

    We use the x-y'-z'' Cardan (intrinsic) convention.

    Parameters
    ----------
    xp, yp, zp : np.ndarray
        Three 3-vectors forming an orthogonal basis defining the rotated frame.

    Returns
    -------
    gamma, beta, alpha : float
        The computed Cardan angles
    """
    
    from scipy import optimize
    
    # right now the implementation uses least squares. This is pretty fast
    # and quite robust, not to mention simpler to implement. That said, the
    # performance could be increased considerably (and prehaps the accuracy)
    # too, if necessary) by going for a geometric implementation.
    # -- TJL June 17, 2051

    # ensure we have unit vectors
    xp = xp / np.linalg.norm(xp)
    yp = yp / np.linalg.norm(yp)
    zp = zp / np.linalg.norm(zp)
    
    Rp = np.array([xp, yp, zp]).T
    assert Rp.shape == (3,3)

    # check orthogonality
    n = np.cross(xp, yp)
    err = np.abs(np.linalg.norm(n) - 1.0)
    if not err < orthog_tol:
        raise RuntimeError('Basis grid element %d is not a rectangular '
                           'array - s and f vectors are not orthogonal' % err)


    def errfunc(args):
        R = _rotation_matrix_from_angles(*args)
        return (R - Rp).flatten()

    #x0 = np.array([0.0, 0.0, 0.0])
    x0 = np.random.rand(3) * 180.0
    ans, _ = optimize.leastsq(errfunc, x0)

    
    for i in range(len(ans)):
        ans[i] = ans[i] % 360.0
        if ans[i] < 0:
            ans[i] += 360.0
        
    err = np.sum(np.square(errfunc(ans)))
    if err > cardan_tol:
        raise RuntimeError('Could not find a consistent set of Cardan angles, '
                           'check input and try again. There is a small chance '
                           'this error is due to a random number, so try running'
                           ' your code one more time to be sure. Err: %e' % err)
    
    gamma, beta, alpha = ans

    if return_units == 'radians':
        alpha = np.radians(alpha)
        beta  = np.radians(beta)
        gamma = np.radians(gamma)
    elif return_units == 'degrees':
        pass
    else:
        raise ValueError('`return_units` must be "radians" or "degrees"')

    return gamma, beta, alpha


