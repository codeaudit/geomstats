"""Visualization for Geometric Statistics."""

from geomstats.hyperbolic_space import HyperbolicSpace
from geomstats.hypersphere import Hypersphere
from geomstats.special_euclidean_group import SpecialEuclideanGroup
from geomstats.special_orthogonal_group import SpecialOrthogonalGroup
from mpl_toolkits.mplot3d import Axes3D  # NOQA

import geomstats.special_orthogonal_group as special_orthogonal_group
import geomstats.vectorization as vectorization
import matplotlib.pyplot as plt
import numpy as np

SE3_GROUP = SpecialEuclideanGroup(n=3)
SO3_GROUP = SpecialOrthogonalGroup(n=3)
S2 = Hypersphere(dimension=2)
H2 = HyperbolicSpace(dimension=2)

AX_SCALE = 1.2

IMPLEMENTED = ['SO3_GROUP', 'SE3_GROUP', 'S2', 'H2']


class Arrow3D():
    "An arrow in 3d, i.e. a point and a vector."
    def __init__(self, point, vector):
        self.point = point
        self.vector = vector

    def draw(self, ax, **quiver_kwargs):
        "Draw the arrow in 3D plot."
        ax.quiver(self.point[0], self.point[1], self.point[2],
                  self.vector[0], self.vector[1], self.vector[2],
                  **quiver_kwargs)


class Trihedron():
    "A trihedron, i.e. 3 Arrow3Ds at the same point."
    def __init__(self, point, vec_1, vec_2, vec_3):
        self.arrow_1 = Arrow3D(point, vec_1)
        self.arrow_2 = Arrow3D(point, vec_2)
        self.arrow_3 = Arrow3D(point, vec_3)

    def draw(self, ax, **arrow_draw_kwargs):
        """
        Draw the trihedron by drawing its 3 Arrow3Ds.
        Arrows are drawn is order using green, red, and blue
        to show the trihedron's orientation.
        """
        if 'color' in arrow_draw_kwargs:
            self.arrow_1.draw(ax, **arrow_draw_kwargs)
            self.arrow_2.draw(ax, **arrow_draw_kwargs)
            self.arrow_3.draw(ax, **arrow_draw_kwargs)
        else:
            self.arrow_1.draw(ax, color='g', **arrow_draw_kwargs)
            self.arrow_2.draw(ax, color='r', **arrow_draw_kwargs)
            self.arrow_3.draw(ax, color='b', **arrow_draw_kwargs)


class Sphere():
    """
    Create the arrays sphere_x, sphere_y, sphere_z of values
    to plot the wireframe of a sphere.
    Their shape is (n_meridians, n_circles_latitude).
    """
    def __init__(self, n_meridians=40, n_circles_latitude=None,
                 points=None):
        if n_circles_latitude is None:
            n_circles_latitude = max(n_meridians / 2, 4)
        u, v = np.mgrid[0:2 * np.pi:n_meridians * 1j,
                        0:np.pi:n_circles_latitude * 1j]

        self.center = np.zeros(3)
        self.radius = 1
        self.sphere_x = self.center[0] + self.radius * np.cos(u) * np.sin(v)
        self.sphere_y = self.center[1] + self.radius * np.sin(u) * np.sin(v)
        self.sphere_z = self.center[2] + self.radius * np.cos(v)

        self.points = []
        if points is not None:
            self.add_points(points)

    def add_points(self, points):
        assert np.all(S2.belongs(points))
        points_list = points.tolist()
        self.points.extend(points_list)

    def draw(self, ax, **scatter_kwargs):
        ax.plot_wireframe(self.sphere_x,
                          self.sphere_y,
                          self.sphere_z,
                          color="black", alpha=0.9)
        self.draw_points(ax, **scatter_kwargs)

    def draw_points(self, ax, **scatter_kwargs):
        points_x = np.vstack([point[0] for point in self.points])
        points_y = np.vstack([point[1] for point in self.points])
        points_z = np.vstack([point[2] for point in self.points])
        ax.scatter(points_x, points_y, points_z, **scatter_kwargs)

    def fibonnaci_points(self, n_points=16000):
        """Spherical Fibonacci point sets yield nearly uniform point
        distributions on the unit sphere."""

        x_vals = []
        y_vals = []
        z_vals = []

        offset = 2. / n_points
        increment = np.pi * (3. - np.sqrt(5.))

        for i in range(n_points):
            y = ((i * offset) - 1) + (offset / 2)
            r = np.sqrt(1 - pow(y, 2))

            phi = ((i + 1) % n_points) * increment

            x = np.cos(phi) * r
            z = np.sin(phi) * r

            x_vals.append(x)
            y_vals.append(y)
            z_vals.append(z)

        x_vals = [(self.radius * i) for i in x_vals]
        y_vals = [(self.radius * i) for i in y_vals]
        z_vals = [(self.radius * i) for i in z_vals]

        return np.array([x_vals, y_vals, z_vals])

    def plot_heatmap(self, ax,
                     scalar_function,
                     n_points=16000,
                     alpha=0.2,
                     cmap='jet'):
        """Plot a heatmap defined by a loss on the sphere."""
        points = self.fibonnaci_points(n_points)
        intensity = np.array([scalar_function(x) for x in points.T])
        ax.scatter(points[0, :], points[1, :], points[2, :],
                   c=intensity,
                   alpha=alpha,
                   marker='.',
                   cmap=plt.get_cmap(cmap))


class PoincareDisk():
    def __init__(self, points=None):
        self.center = np.array([0., 0.])
        self.points = []
        if points is not None:
            self.add_points(points)

    def add_points(self, points):
        assert np.all(H2.belongs(points))
        points = self.convert_to_disk_coordinates(points)
        points_list = points.tolist()
        self.points.extend(points_list)

    def convert_to_disk_coordinates(self, points):
        disk_coords = points[:, 1:] / (1 + points[:, :1])
        return disk_coords

    def draw(self, ax, **kwargs):
        circle = plt.Circle((0, 0), radius=1., color='black', fill=False)
        ax.add_artist(circle)
        points_x = np.vstack([point[0] for point in self.points])
        points_y = np.vstack([point[1] for point in self.points])
        ax.scatter(points_x, points_y, **kwargs)


def convert_to_trihedron(point, space=None):
    """
    Transform a rigid pointrmation
    into a trihedron s.t.:
    - the trihedron's base point is the translation of the origin
    of R^3 by the translation part of point,
    - the trihedron's orientation is the rotation of the canonical basis
    of R^3 by the rotation part of point.
    """
    point = vectorization.to_ndarray(point, to_ndim=2)
    n_points, _ = point.shape

    dim_rotations = SO3_GROUP.dimension

    if space is 'SE3_GROUP':
        rot_vec = point[:, :dim_rotations]
        translation = point[:, dim_rotations:]
    elif space is 'SO3_GROUP':
        rot_vec = point
        translation = np.zeros((n_points, 3))
    else:
        raise NotImplementedError(
                'Trihedrons are only implemented for SO(3) and SE(3).')

    rot_mat = SO3_GROUP.matrix_from_rotation_vector(rot_vec)
    rot_mat = special_orthogonal_group.closest_rotation_matrix(rot_mat)
    basis_vec_1 = np.array([1, 0, 0])
    basis_vec_2 = np.array([0, 1, 0])
    basis_vec_3 = np.array([0, 0, 1])

    trihedrons = []
    for i in range(n_points):
        trihedron_vec_1 = np.dot(rot_mat[i], basis_vec_1)
        trihedron_vec_2 = np.dot(rot_mat[i], basis_vec_2)
        trihedron_vec_3 = np.dot(rot_mat[i], basis_vec_3)
        trihedron = Trihedron(translation[i],
                              trihedron_vec_1,
                              trihedron_vec_2,
                              trihedron_vec_3)
        trihedrons.append(trihedron)
    return trihedrons


def plot(points, ax=None, space=None, **point_draw_kwargs):
    """
    Plot points in the 3D Special Euclidean Group,
    by showing them as trihedrons.
    """
    if space not in IMPLEMENTED:
        raise NotImplementedError(
                'The plot function is not implemented'
                ' for space {}. The spaces available for visualization'
                ' are: {}.'.format(space, IMPLEMENTED))

    if points is None:
        raise ValueError("No points given for plotting.")

    points = vectorization.to_ndarray(points, to_ndim=2)

    if ax is None:
        if space is 'SE3_GROUP':
            ax_s = AX_SCALE * np.amax(np.abs(points[:, 3:6]))
        elif space is 'SO3_GROUP':
            ax_s = AX_SCALE * np.amax(np.abs(points[:, :3]))
        else:
            ax_s = AX_SCALE

        if space is 'H2':
            ax = plt.subplot(aspect='equal')
            plt.setp(ax,
                     xlim=(-ax_s, ax_s),
                     ylim=(-ax_s, ax_s),
                     xlabel='X', ylabel='Y')

        else:
            # The 3d projection needs the Axes3d module import.
            ax = plt.subplot(111, projection='3d', aspect='equal')
            plt.setp(ax,
                     xlim=(-ax_s, ax_s),
                     ylim=(-ax_s, ax_s),
                     zlim=(-ax_s, ax_s),
                     xlabel='X', ylabel='Y', zlabel='Z')

    if space in ('SO3_GROUP', 'SE3_GROUP'):
        trihedrons = convert_to_trihedron(points, space=space)
        for t in trihedrons:
            t.draw(ax, **point_draw_kwargs)

    elif space is 'S2':
        sphere = Sphere()
        sphere.add_points(points)
        sphere.draw(ax, **point_draw_kwargs)

    elif space is 'H2':
        poincare_disk = PoincareDisk()
        poincare_disk.add_points(points)
        poincare_disk.draw(ax, **point_draw_kwargs)

    return ax
