from tkinter import *
import math
import numpy as np
from sympy import Point, Polygon
import time

'''================= Your classes and methods ================='''

# These functions will help you to check collisions with obstacles

def rotate(points, angle, center):
    angle = math.radians(angle)
    cos_val = math.cos(angle)
    sin_val = math.sin(angle)
    cx, cy = center
    new_points = []

    for x_old, y_old in points:
        x_old -= cx
        y_old -= cy
        x_new = x_old * cos_val - y_old * sin_val
        y_new = x_old * sin_val + y_old * cos_val
        new_points.append((x_new+cx, y_new+cy))

    return new_points

def get_polygon_from_position(position):
    x,y,yaw = position
    points = [(x - 50, y - 100), (x + 50, y - 100), (x + 50, y + 100), (x - 50, y + 100)] 
    new_points = rotate(points, yaw * 180 / math.pi, (x,y))

    return Polygon(*list(map(Point, new_points)))

def get_polygon_from_obstacle(obstacle):
    points = [(obstacle[0], obstacle[1]), (obstacle[2], obstacle[3]), (obstacle[4], obstacle[5]), (obstacle[6], obstacle[7])] 
    return Polygon(*list(map(Point, points)))

def get_polygon_from_grid_cell(center):
    x = center[0]
    y = center[1]
    points = [(x - 25, y - 25), (x + 25, y - 25),
              (x + 25, y + 25), (x - 25, y + 25)]
    return Polygon(*list(map(Point, points)))

def collides(position, obstacle):
    return get_polygon_from_position(position).intersection(get_polygon_from_obstacle(obstacle))


def distance(p1, p2):
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def create_nodes(grid):
    graph = {}
    for h in range(grid.shape[0]):
        for w in range(grid.shape[1]):
            new_node = Node([h, w])
            new_node.g = h + w
            graph[str(h) + str(w)] = new_node

    return graph


def node_neighbors(graph, grid, grid_point):
    neighbors = []

    for h in range(max(0, grid_point[0] - 1), min(grid.shape[0], grid_point[0] + 2)):
        for w in range(max(0, grid_point[1] - 1), min(grid.shape[1], grid_point[1] + 2)):
            if grid[h, w] != -1:
                neighbors.append([h, w])

    if grid_point in neighbors:
        neighbors.remove(grid_point)

    neighbors_nodes = [graph[str(point[0]) + str(point[1])] for point in neighbors]

    return neighbors_nodes

class Node:
    def __init__(self, point):
        self.name = str(point[0]) + str(point[1])
        self.point = point
        self.h = 0.
        self.g = 0.
        

class Window():

    def __init__(self):
        self.root = Tk()
        self.car_angle = 0
        self.root.title("")
        self.width  = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        self.root.geometry(f'{self.width}x{self.height}')
        self.canvas = Canvas(self.root, bg="#777777", height=self.height, width=self.width)
        self.canvas.pack()
        self.path_block_ids = []
        # self.points = [0, 500, 500/2, 0, 500, 500]

    def occupied_cells(self, grid):
        x_centers = grid[0]
        y_centers = grid[1]
        height = x_centers.shape[0]
        width = x_centers.shape[1]
        occupied = np.zeros((height, width))

        centers_of_obstacles = self.obstacle_centers()
        xy_ranges = [[[int(max(0, (x - 200) // 50)), int(min(width * 50, x + 200) // 50)],
                      [int(max(0, (y - 200) // 50)), int(min(height * 50, y + 200) // 50)]]
                     for x, y in centers_of_obstacles]
        obstacle_polygons = [get_polygon_from_obstacle(obstacle) for obstacle in self.get_obstacles()]

        for xy in xy_ranges:
            x_range = xy[0]
            y_range = xy[1]
            x_range = list(range(*x_range))
            y_range = list(range(*y_range))
            x_c = x_centers[:, x_range][y_range, :]
            y_c = y_centers[:, x_range][y_range, :]

            for i, x in enumerate(x_range):
                for j, y in enumerate(y_range):
                    cell_polygon = get_polygon_from_grid_cell([x_c[j, i], y_c[j, i]])
                    for obstacle in obstacle_polygons:
                            if cell_polygon.intersection(obstacle):
                                occupied[y, x] = -1

            obstacle_idx = np.where(occupied == -1)
            x_idx = obstacle_idx[0]
            y_idx = obstacle_idx[1]

            occupied[np.minimum(occupied.shape[0], x_idx + 1), y_idx] = -1
            occupied[np.maximum(0, x_idx - 1), y_idx] = -1
            occupied[x_idx, np.minimum(occupied.shape[1], y_idx + 1)] = -1
            occupied[x_idx, np.maximum(0, y_idx - 1)] = -1

        return occupied

    def rotate_car(self, angle):
        self.car_angle += angle
        car = self.canvas.coords(2)
        car_center = self.get_center(2)
        car_coords = [(x, y) for x, y in zip(car[0::2], car[1::2])]
        rotated_car = self.rotate(car_coords, angle, car_center)
        self.canvas.coords(2, *rotated_car)
        return

    def move_car(self, distance):
        angle = self.get_yaw(2)
        cos_val = math.cos(angle)
        sin_val = math.sin(angle)

        x_distance = distance * sin_val
        y_distance = -distance * cos_val

        self.canvas.move(2, x_distance, y_distance)

        return

    def make_grid(self):
        hdim = self.height // 50
        wdim = self.width // 50

        x_centers = np.array([[25 + 50 * x for x in range(wdim)] for k in range(hdim)])
        y_centers = np.array([[25 + 50 * k for y in range(wdim)] for k in range(hdim)])

        return x_centers, y_centers

    def point_to_grid(self, coord):
        width_grid = int(coord[0] // 50)
        height_grid = int(coord[1] // 50)

        return height_grid, width_grid

    def AStar(self, grid):
        start = self.point_to_grid(self.get_start_position())
        target = self.point_to_grid(self.get_target_position())

        hdim = self.height // 50
        wdim = self.width // 50

        cell_centers = np.array([[[25 + 50 * i, 25 + 50 * j] for j in range(wdim)] for i in range(hdim)])

        graph = create_nodes(grid)
        start_node = graph[str(start[0]) + str(start[1])]
        end_node = graph[str(target[0]) + str(target[1])]
        end_node_coords = cell_centers[end_node.point[0], end_node.point[1]]
        queue = set()
        visited = set()
        queue.add(start_node)
        path = []

        while len(queue) > 0:
            current_node = min(queue, key=lambda node: node.h + node.g)
            path.append(current_node.point)
            # print(current_node.point)
            queue.remove(current_node)
            visited.add(current_node)

            if current_node == end_node:
                break

            current_neighbors = node_neighbors(graph, grid, current_node.point)

            for next_node in current_neighbors:
                if next_node not in visited:
                    node_xy = cell_centers[next_node.point[0], next_node.point[1]]
                    next_node.h = distance(node_xy, end_node_coords)
                    # print(f'Distance from node {next_node.name} to end: {next_node.h} from point {node_xy}')
                    queue.add(next_node)

        return path

        
    '''================= Your Main Function ================='''


    def go(self, event):
    
        # Write your code here
        for id in self.path_block_ids:
            self.canvas.delete(id)
                
        print("Start position:", self.get_start_position())
        print("Target position:", self.get_target_position()) 
        print("Obstacles:", self.get_obstacles())

        cell_centers = self.make_grid()
        occupied_cells = self.occupied_cells(cell_centers)

        path = self.AStar(occupied_cells)
        print(path)

        hdim = self.height // 50
        wdim = self.width // 50

        cell_centers = np.array([[[25 + 50 * i, 25 + 50 * j] for j in range(wdim)] for i in range(hdim)])

        for coord in path:
            h = coord[0]
            w = coord[1]

            center = cell_centers[h, w]
            next_x = center[1]
            next_y = center[0]
            car_x = self.get_center(2)[0]
            car_y = self.get_center(2)[1]

            angle = 180 * (np.arctan2(car_y - next_y, car_x - next_x)) / math.pi - 90
            distance = self.distance(car_x, car_y, next_x, next_y)

            #self.rotate_car(angle)
            #self.move_car(distance)
            #time.sleep(1)


        for coord in path:
            h = coord[0]
            w = coord[1]

            center = cell_centers[h, w]
            x_center = center[1]
            y_center = center[0]

            self.create_path_block(x_center, y_center)

        # Example of collision calculation

        number_of_collisions = 0
        for obstacle in self.get_obstacles():
            if collides(self.get_start_position(), obstacle):
                number_of_collisions += 1
        print("Start position collides with", number_of_collisions, "obstacles")
        
        
    '''================= Interface Methods ================='''
    
    def get_obstacles(self) :
        obstacles = []
        potential_obstacles = self.canvas.find_all()
        for i in potential_obstacles:
            if (i > 2) :
                coords = self.canvas.coords(i)
                if coords:
                    obstacles.append(coords)
        return obstacles

    def obstacle_centers(self):
        center_x, center_y = None, None
        centers = []
        potential_obstacles = self.canvas.find_all()
        for i in potential_obstacles:
            if (i > 2) :
                coords = self.canvas.coords(i)
                if coords:
                    center_x, center_y = ((coords[0] + coords[4]) / 2, (coords[1] + coords[5]) / 2)
                    centers.append([center_x, center_y])

        return centers

    def get_start_position(self) :
        x,y = self.get_center(2) # Purple block has id 2
        yaw = self.get_yaw(2)
        return x,y,yaw
    
    def get_target_position(self) :
        x,y = self.get_center(1) # Green block has id 1 
        yaw = self.get_yaw(1)
        return x,y,yaw 

    def get_center(self, id_block):
        coords = self.canvas.coords(id_block)
        center_x, center_y = ((coords[0] + coords[4]) / 2, (coords[1] + coords[5]) / 2)
        return [center_x, center_y]

    def get_yaw(self, id_block):
        center_x, center_y = self.get_center(id_block)
        first_x = 0.0
        first_y = -1.0
        second_x = 1.0
        second_y = 0.0
        points = self.canvas.coords(id_block)
        end_x = (points[0] + points[2])/2
        end_y = (points[1] + points[3])/2
        direction_x = end_x - center_x
        direction_y = end_y - center_y
        length = math.hypot(direction_x, direction_y)
        unit_x = direction_x / length
        unit_y = direction_y / length
        cos_yaw = unit_x * first_x + unit_y * first_y 
        sign_yaw = unit_x * second_x + unit_y * second_y
        if (sign_yaw >= 0 ) :
            return math.acos(cos_yaw)
        else :
            return -math.acos(cos_yaw)
       
    def get_vertices(self, id_block):
        return self.canvas.coords(id_block)

    '''=================================================='''

    def rotate(self, points, angle, center):
        angle = math.radians(angle)
        cos_val = math.cos(angle)
        sin_val = math.sin(angle)
        cx, cy = center
        new_points = []

        for x_old, y_old in points:
            x_old -= cx
            y_old -= cy
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append(x_new+cx)
            new_points.append(y_new+cy)

        return new_points

    def start_block(self, event):
        widget = event.widget
        widget.start_x = event.x
        widget.start_y = event.y

    def in_rect(self, point, rect):
        x_start, x_end = min(rect[::2]), max(rect[::2])
        y_start, y_end = min(rect[1::2]), max(rect[1::2])

        if x_start < point[0] < x_end and y_start < point[1] < y_end:
            return True

    def motion_block(self, event):
        widget = event.widget

        for i in range(1, 10):
            if widget.coords(i) == []:
                break
            if self.in_rect([event.x, event.y], widget.coords(i)):
                coords = widget.coords(i)
                id = i
                break

        res_cords = []
        try:
            coords
        except:
            return

        for ii, i in enumerate(coords):
            if ii % 2 == 0:
                res_cords.append(i + event.x - widget.start_x)
            else:
                res_cords.append(i + event.y - widget.start_y)

        widget.start_x = event.x
        widget.start_y = event.y
        widget.coords(id, res_cords)
        widget.center = ((res_cords[0] + res_cords[4]) / 2, (res_cords[1] + res_cords[5]) / 2)

    def draw_block(self, points, color):
        x = self.canvas.create_polygon(points, fill=color)
        return x

    def distance(self, x1, y1, x2, y2):
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def set_id_block(self, event):
        widget = event.widget

        for i in range(1, 10):
            if widget.coords(i) == []:
                break
            if self.in_rect([event.x, event.y], widget.coords(i)):
                coords = widget.coords(i)
                id = i
                widget.id_block = i
                break

        widget.center = ((coords[0] + coords[4]) / 2, (coords[1] + coords[5]) / 2)

    def rotate_block(self, event):
        angle = 0
        widget = event.widget

        if widget.id_block == None:
            for i in range(1, 10):
                if widget.coords(i) == []:
                    break
                if self.in_rect([event.x, event.y], widget.coords(i)):
                    coords = widget.coords(i)
                    id = i
                    widget.id_block == i
                    break
        else:
            id = widget.id_block
            coords = widget.coords(id)

        wx, wy = event.x_root, event.y_root
        try:
            coords
        except:
            return

        block = coords
        center = widget.center
        x, y = block[2], block[3]

        cat1 = self.distance(x, y, block[4], block[5])
        cat2 = self.distance(wx, wy, block[4], block[5])
        hyp = self.distance(x, y, wx, wy)

        if wx - x > 0: angle = math.acos((cat1**2 + cat2**2 - hyp**2) / (2 * cat1 * cat2))
        elif wx - x < 0: angle = -math.acos((cat1**2 + cat2**2 - hyp**2) / (2 * cat1 * cat2))

        new_block = self.rotate([block[0:2], block[2:4], block[4:6], block[6:8]], angle, center)
        self.canvas.coords(id, new_block)

    def delete_block(self, event):
        widget = event.widget.children["!canvas"]

        for i in range(1, 10):
            if widget.coords(i) == []:
                break
            if self.in_rect([event.x, event.y], widget.coords(i)):
                widget.coords(i, [0,0])
                break

    def create_block(self, event):
        block = [[0, 100], [100, 100], [100, 300], [0, 300]]

        id = self.draw_block(block, "black")

        self.canvas.tag_bind(id, "<Button-1>", self.start_block)
        self.canvas.tag_bind(id, "<Button-3>", self.set_id_block)
        self.canvas.tag_bind(id, "<B1-Motion>", self.motion_block)
        self.canvas.tag_bind(id, "<B3-Motion>", self.rotate_block)

    def make_draggable(self, widget):
        widget.bind("<Button-1>", self.drag_start)
        widget.bind("<B1-Motion>", self.drag_motion)

    def drag_start(self, event):
        widget = event.widget
        widget.start_x = event.x
        widget.start_y = event.y

    def drag_motion(self, event):
        widget = event.widget
        x = widget.winfo_x() - widget.start_x + event.x + 200
        y = widget.winfo_y() - widget.start_y + event.y + 100
        widget.place(rely=0.0, relx=0.0, x=x, y=y)

    def create_button_create(self):
        button = Button(
            text="New",
            bg="#555555",
            activebackground="blue",
            borderwidth=0
        )

        button.place(rely=0.0, relx=0.0, x=200, y=100, anchor=SE, width=200, height=100)
        button.bind("<Button-1>", self.create_block)

    def create_path_block(self, center_x, center_y):
        block = [[center_x - 10, center_y - 10],
                 [center_x + 10, center_y - 10],
                 [center_x + 10, center_y + 10],
                 [center_x - 10, center_y - 10]]

        id = self.draw_block(block, "yellow")
        self.path_block_ids.append(id)

        return


    def create_green_block(self, center_x):
        block = [[center_x - 50, 100],
                 [center_x + 50, 100],
                 [center_x + 50, 300],
                 [center_x - 50, 300]]

        id = self.draw_block(block, "green")

        self.canvas.tag_bind(id, "<Button-1>", self.start_block)
        self.canvas.tag_bind(id, "<Button-3>", self.set_id_block)
        self.canvas.tag_bind(id, "<B1-Motion>", self.motion_block)
        self.canvas.tag_bind(id, "<B3-Motion>", self.rotate_block)

    def create_purple_block(self, center_x, center_y):
        block = [[center_x - 50, center_y - 300],
                 [center_x + 50, center_y - 300],
                 [center_x + 50, center_y - 100],
                 [center_x - 50, center_y - 100]]

        id = self.draw_block(block, "purple")

        self.canvas.tag_bind(id, "<Button-1>", self.start_block)
        self.canvas.tag_bind(id, "<Button-3>", self.set_id_block)
        self.canvas.tag_bind(id, "<B1-Motion>", self.motion_block)
        self.canvas.tag_bind(id, "<B3-Motion>", self.rotate_block)

    def create_button_go(self):
        button = Button(
            text="Go",
            bg="#555555",
            activebackground="blue",
            borderwidth=0
        )

        button.place(rely=0.0, relx=1.0, x=0, y=200, anchor=SE, width=100, height=200)
        button.bind("<Button-1>", self.go)

    def run(self):
        root = self.root

        self.create_button_create()
        self.create_button_go()
        self.create_green_block(self.width/2)
        self.create_purple_block(self.width/2, self.height)

        root.bind("<Delete>", self.delete_block)

        root.mainloop()

    
if __name__ == "__main__":
    run = Window()
    run.run()
