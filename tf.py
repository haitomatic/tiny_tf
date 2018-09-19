import numpy as np
import transformations as tft


class TFTree(object):
    def __init__(self):
        self.nodes = {}

    def add_transform(self, parent, child, xform):
        if parent not in self.nodes:
            self.nodes[parent] = TFNode(parent, None, None)

        if child not in self.nodes:
            self.nodes[child] = TFNode(child, self.nodes[parent], xform)
        else:
            node = self.nodes[child]
            node.parent = self.nodes[parent]
            node.transform = xform

    def lookup_transform(self, frame, target):
        if frame not in self.nodes:
            raise Exception("frame is not part of the tf tree")
        if target not in self.nodes:
            raise Exception("target is not part of the tf tree")
        if frame == target:
            return Transform(0, 0, 0, 0, 0, 0, 1)

        parent_nodes = []

        for name, node in self.nodes.items():
            if not node.parent:
                parent_nodes.append(node)

        if len(parent_nodes) > 1:
            raise Exception("More than one tree found, this case is unsupported")
        if len(parent_nodes) == 0:
            raise Exception("No parent node found, there are probably cycles in the tree")

        parent_node = parent_nodes[0]

        frame_path_to_parent = self._get_path_to_parent(parent_node, frame)
        target_path_to_parent = self._get_path_to_parent(parent_node, target)

        while True:
            if frame_path_to_parent[-1] == target_path_to_parent[-1]:
                frame_path_to_parent.pop()
                target_path_to_parent.pop()
            else:
                break

        def get_inverse_xform_for_path(path):
            transform_to_parent = np.identity(4)
            for node in path:
                transform_to_parent = np.dot(np.linalg.inv(node.transformation_matrix),
                                                        transform_to_parent)
            return transform_to_parent

        frame_transform_to_common_parent = get_inverse_xform_for_path(frame_path_to_parent)
        target_transform_to_common_parent = get_inverse_xform_for_path(target_path_to_parent)

        return np.dot(np.linalg.inv(target_transform_to_common_parent), frame_transform_to_common_parent)

    def _get_path_to_parent(self, parent_node, node_name):
        node = self.nodes[node_name]
        traversed_nodes = {}
        path = []
        while True:
            if node in traversed_nodes:
                raise Exception("Cycle detected, this case is unsupported")
            traversed_nodes[node] = True
            path.append(node)
            node = node.parent
            if node == parent_node:
                break

        return path

class TFNode(object):
    def __init__(self, name, parent, transform):
        self.parent = parent
        self.name = name
        self.transform = transform

    @property
    def transformation_matrix(self):
        if not self.transform:
            return np.identity(4)
        return self.transform.matrix


class Transform(object):
    def __init__(self, x, y, z, qx, qy, qz, qw):
        self.x = x
        self.y = x
        self.z = x
        self.qx = qx
        self.qy = qy
        self.qz = qz
        self.qw = qw

    @classmethod
    def from_matrix(cls, mat):
        x, y, z = mat[0:3, -1]
        qx, qy, qz, qw = tft.quaternion_from_matrix(mat[0:3, 0:3])
        return cls(x, y, z, qx, qy, qz, qw)

    @classmethod
    def from_position_euler(cls, x, y, z, roll, pitch, yaw):
        qx, qy, qz, qw = tft.quaternion_from_euler((roll, pitch, yaw))

    @property
    def matrix(self):
        out = np.identity(4)
        out[0:3, 0:3] = self.rotation_matrix
        out[0, -1] = self.x
        out[1, -1] = self.y
        out[2, -1] = self.z
        return out

    @property
    def rotation_matrix(self):
        return tft.quaternion_matrix(self.quaternion)

    @property
    def position(self):
        return self.x, self.y, self.z

    @property
    def euler(self):
        return tft.euler_from_quaternion(self.quaternion)

    @property
    def quaternion(self):
        return (self.qx, self.qy, self.qz, self.qw)
