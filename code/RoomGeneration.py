import random

MOB_TYPES = ["Zombie", "Creeper", "Spider", "Skeleton"]

def generate_room(width=20, length=20, test = True):
    room = '''<DrawCuboid x1="{}" y1="63" z1="{}" x2="{}" y2="70" z2="{}" type="iron_block"/>
    <DrawCuboid x1="{}" y1="64" z1="{}" x2="{}" y2="69" z2="{}" type="air"/>
    <DrawCuboid x1="{}" y1="70" z1="{}" x2="{}" y2="70" z2="{}" type="glowstone"/>'''
    room = room.format(int(width/2), int(length/2), -int(width/2), -int(length/2), 
                       int(width/2)-1, int(length/2)-1, -int(width/2)+1, -int(length/2)+1,
                       int(width/2)-1, int(length/2)-1, -int(width/2)+1, -int(length/2)+1)

    if test:
        room += '<DrawEntity x="4" y="64" z="6" type="Zombie"/>'
    else:
        for _ in range(3):
            monster = random.choice(MOB_TYPES)
            x_pos = random.randint(-8, 8)
            z_pos = random.randint(-2, 8)
            room += '<DrawEntity x="' + str(x_pos) + '" y="64" z="' + str(z_pos) + '" type="' + monster + '"/>'


    return room