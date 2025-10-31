import arcade
import math

SCREEN_TITLE = "Dice Walk"
GRID_SIZE = 8
EDGE_COLOR = (0, 200, 255)


class DiceWalkGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, SCREEN_TITLE, fullscreen=True)
        self.set_fullscreen(True)
        self.screen_width, self.screen_height = self.get_size()
        arcade.set_background_color(arcade.color.BLACK)
        self.tile_height = 0.7 * self.screen_height / (GRID_SIZE - 1)
        self.tile_width = 2 * self.tile_height
        self.origin_x = self.screen_width / 2
        self.origin_y = self.screen_height / 2 - (GRID_SIZE - 1) * self.tile_height / 2
        self.grid_lines = []
        self._build_grid()
        self.cube_i = GRID_SIZE // 2
        self.cube_j = GRID_SIZE // 2
        self.animating = False
        self.anim_type = 'slide'
        self.anim_start_x = 0.0
        self.anim_start_y = 0.0
        self.anim_target_x = 0.0
        self.anim_target_y = 0.0
        self.anim_elapsed = 0.0
        self.anim_duration = 0.35
        self.anim_di = 0
        self.anim_dj = 0
        self.anim_start_i = self.cube_i
        self.anim_start_j = self.cube_j
        self.paused = False
        self.faces = {
            'top': 'yellow',
            'bottom': 'gray',
            'north': 'green',
            'south': 'blue',
            'east': 'red',
            'west': 'magenta',
        }
        self.face_colors = {
            'yellow': (255, 255, 0),
            'gray': (128, 128, 128),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'red': (255, 0, 0),
            'magenta': (255, 0, 255),
        }
        self._faces_snapshot = None

    def _iso_point(self, i: float, j: float):
        x = self.origin_x + (i - j) * (self.tile_width / 2)
        y = self.origin_y + (i + j) * (self.tile_height / 2)
        return x, y

    def _tile_center(self, i: int, j: int):
        return self._iso_point(i + 0.5, j + 0.5)

    def _build_grid(self):
        lines = []
        for i in range(GRID_SIZE + 1):
            lines.append((*self._iso_point(i, 0), *self._iso_point(i, GRID_SIZE)))
        for j in range(GRID_SIZE + 1):
            lines.append((*self._iso_point(0, j), *self._iso_point(GRID_SIZE, j)))
        self.grid_lines = lines

    def on_draw(self):
        self.clear()
        for (x1, y1, x2, y2) in self.grid_lines:
            arcade.draw_line(x1, y1, x2, y2, arcade.color.WHITE, 1)
        
        if self.animating:
            t = min(self.anim_elapsed / self.anim_duration, 1.0)
            if self.anim_type == 'slide':
                cx = self.anim_start_x + (self.anim_target_x - self.anim_start_x) * t
                cy = self.anim_start_y + (self.anim_target_y - self.anim_start_y) * t
                self._draw_cube_standing(cx, cy)
            else:
                self._draw_cube_tumble(t)
            if t >= 1.0 and not self.paused:
                self.animating = False
                if self.anim_type == 'tumble':
                    self._commit_orientation()
                self.anim_type = 'slide'
        else:
            cx, cy = self._tile_center(self.cube_i, self.cube_j)
            self._draw_cube_standing(cx, cy)

    def _draw_cube_standing(self, cx: float, cy: float):
        scale = 0.8
        half = 0.5 * scale
        height = scale
        ci0 = self.cube_i + 0.5
        cj0 = self.cube_j + 0.5
        verts = [
            [ci0 - half, cj0 - half, 0.0], [ci0 - half, cj0 + half, 0.0],
            [ci0 + half, cj0 - half, 0.0], [ci0 + half, cj0 + half, 0.0],
            [ci0 - half, cj0 - half, height], [ci0 - half, cj0 + half, height],
            [ci0 + half, cj0 - half, height], [ci0 + half, cj0 + half, height],
        ]
        face_defs = [
            ([0,1,3,2], 'bottom'), ([4,5,7,6], 'top'),
            ([0,1,5,4], 'west'), ([2,3,7,6], 'east'),
            ([0,2,6,4], 'south'), ([1,3,7,5], 'north'),
        ]
        screen=[]
        for (vi,vj,vz) in verts:
            sx, sy = self._iso_point(vi, vj); sy += vz * self.tile_height
            screen.append((sx, sy))
        faces_to_draw=[]
        for face, logical in face_defs:
            depth=sum(screen[i][1] for i in face)/len(face)
            faces_to_draw.append((depth, face, logical))
        
        position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'west': 4, 'top': 5}
        faces_to_draw.sort(key=lambda x: position_priority.get(x[2], 99))
        
        e=EDGE_COLOR
        for _, face, position in faces_to_draw:
            poly=[screen[i] for i in face]
            face_id = self.faces.get(position, 'gray')
            color = self.face_colors.get(face_id, (80,80,80))
            arcade.draw_polygon_filled(poly, color)
            for i in range(len(face)):
                a=face[i]; b=face[(i+1)%len(face)]
                p1=screen[a]; p2=screen[b]
                arcade.draw_line(p1[0], p1[1], p2[0], p2[1], e,2)

    def _draw_cube_tumble(self, t: float):
        angle = (math.pi / 2) * t
        si = self.anim_start_i; sj = self.anim_start_j
        di = self.anim_di; dj = self.anim_dj
        scale = 0.8
        half = 0.5 * scale
        height = scale
        ci0 = si + 0.5; cj0 = sj + 0.5
        verts = [
            [ci0 - half, cj0 - half, 0.0], [ci0 - half, cj0 + half, 0.0],
            [ci0 + half, cj0 - half, 0.0], [ci0 + half, cj0 + half, 0.0],
            [ci0 - half, cj0 - half, height], [ci0 - half, cj0 + half, height],
            [ci0 + half, cj0 - half, height], [ci0 + half, cj0 + half, height],
        ]
        if di != 0:
            pivot_i = ci0 + half * di
            for v in verts:
                i_off = v[0] - pivot_i; z = v[2]
                sin_sign = -1 if di == 1 else 1
                v[0] = pivot_i + i_off * math.cos(angle) - z * math.sin(angle) * sin_sign
                v[2] = i_off * math.sin(angle) * sin_sign + z * math.cos(angle)
        elif dj != 0:
            pivot_j = cj0 + half * dj
            for v in verts:
                j_off = v[1] - pivot_j; z = v[2]
                sin_sign = -1 if dj == 1 else 1
                v[1] = pivot_j + j_off * math.cos(angle) - z * math.sin(angle) * sin_sign
                v[2] = j_off * math.sin(angle) * sin_sign + z * math.cos(angle)
        face_defs = [
            ([0,1,3,2], 'bottom'), ([4,5,7,6], 'top'),
            ([0,1,5,4], 'west'), ([2,3,7,6], 'east'),
            ([0,2,6,4], 'south'), ([1,3,7,5], 'north'),
        ]
        screen = []
        for (vi, vj, vz) in verts:
            sx, sy = self._iso_point(vi, vj); sy += vz * self.tile_height
            screen.append((sx, sy))
        
        faces_to_draw=[]
        for face, logical in face_defs:
            depth=sum(screen[i][1] for i in face)/len(face)
            faces_to_draw.append((depth, face, logical))
        
        if di == 1 or dj == 1:
            position_priority = {'north': 0, 'east': 1, 'bottom': 2, 'top': 3, 'south': 4, 'west': 5}
        elif dj == 1:
            position_priority = {'north': 0, 'east': 1, 'bottom': 2, 'top': 3, 'south': 4, 'west': 5}
        elif di == -1:
            position_priority = {'north': 0, 'bottom': 1, 'east': 2, 'west': 3, 'south': 4, 'top': 5}
        elif dj == -1:
            position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'top': 4, 'west': 5}
        else:
            position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'west': 4, 'top': 5}
        
        faces_to_draw.sort(key=lambda x: (position_priority.get(x[2], 99)))
        
        e=EDGE_COLOR
        for _, face, position in faces_to_draw:
            poly=[screen[i] for i in face]
            active_faces = self._faces_snapshot if (self._faces_snapshot is not None and self.animating and self.anim_type=='tumble') else self.faces
            face_id = active_faces.get(position, 'gray')
            color = self.face_colors.get(face_id, (80,80,80))
            arcade.draw_polygon_filled(poly, color)
            for i in range(len(face)):
                a=face[i]; b=face[(i+1)%len(face)]
                p1=screen[a]; p2=screen[b]
                arcade.draw_line(p1[0], p1[1], p2[0], p2[1], e,2)

    def _commit_orientation(self):
        di=self.anim_di; dj=self.anim_dj; f=self.faces
        if di==1:
            f['top'],f['east'],f['bottom'],f['west']=f['west'],f['top'],f['east'],f['bottom']
        elif di==-1:
            f['top'],f['west'],f['bottom'],f['east']=f['east'],f['top'],f['west'],f['bottom']
        elif dj==1:
            f['top'],f['north'],f['bottom'],f['south']=f['south'],f['top'],f['north'],f['bottom']
        elif dj==-1:
            f['top'],f['south'],f['bottom'],f['north']=f['north'],f['top'],f['south'],f['bottom']
        self._faces_snapshot = None

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.close()
        if key == arcade.key.P:
            self.paused = not self.paused
            return
        if self.animating:
            return
        di=dj=0
        if key==arcade.key.UP: dj=1
        elif key==arcade.key.DOWN: dj=-1
        elif key==arcade.key.RIGHT: di=1
        elif key==arcade.key.LEFT: di=-1
        if di!=0 or dj!=0:
            ni=self.cube_i+di; nj=self.cube_j+dj
            if 0<=ni<GRID_SIZE and 0<=nj<GRID_SIZE:
                self.anim_type='tumble'
                self.anim_di=di; self.anim_dj=dj
                self.anim_start_i=self.cube_i; self.anim_start_j=self.cube_j
                self.anim_start_x,self.anim_start_y=self._tile_center(self.cube_i,self.cube_j)
                self.anim_target_x,self.anim_target_y=self._tile_center(ni,nj)
                self.anim_elapsed=0.0; self.animating=True
                self._faces_snapshot = dict(self.faces)
                self.cube_i,self.cube_j=ni,nj

    def on_update(self, delta_time: float):
        if self.animating and not self.paused:
            self.anim_elapsed += delta_time


def main():
    DiceWalkGame()
    arcade.run()


if __name__ == '__main__':
    main()
