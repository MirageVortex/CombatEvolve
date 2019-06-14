import random

MOB_TYPES = ["Zombie", "Skeleton"]

def generate_room(width=20, length=20, monsters = 1):
    room = '''<DrawCuboid x1="{}" y1="63" z1="{}" x2="{}" y2="70" z2="{}" type="iron_block"/>
    <DrawCuboid x1="{}" y1="64" z1="{}" x2="{}" y2="69" z2="{}" type="air"/>
    <DrawCuboid x1="{}" y1="70" z1="{}" x2="{}" y2="70" z2="{}" type="glowstone"/>'''
    room = room.format(int(width/2), int(length/2), -int(width/2), -int(length/2), 
                       int(width/2)-1, int(length/2)-1, -int(width/2)+1, -int(length/2)+1,
                       int(width/2)-1, int(length/2)-1, -int(width/2)+1, -int(length/2)+1)

    for _ in range(monsters):
        monster = random.choice(MOB_TYPES)
        x_pos = 0
        z_pos = 5
        room += '<DrawEntity x="' + str(x_pos) + '" y="64" z="' + str(z_pos) + '" type="' + monster + '"/>'
        x_pos -= 1
        z_pos += 1


    return room