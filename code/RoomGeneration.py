enemys = ["Zombie", "Creeper", "Spider"]

def generate_room(width=20, length=20, monster_count=1):
    room = '''<DrawCuboid x1="{}" y1="63" z1="{}" x2="{}" y2="70" z2="{}" type="iron_block"/>
    <DrawCuboid x1="{}" y1="64" z1="{}" x2="{}" y2="69" z2="{}" type="air"/>
    <DrawCuboid x1="{}" y1="70" z1="{}" x2="{}" y2="70" z2="{}" type="glowstone"/>'''
    room = room.format(int(width/2), int(length/2), -int(width/2), -int(length/2), 
                       int(width/2)-1, int(length/2)-1, -int(width/2)+1, -int(length/2)+1,
                       int(width/2)-1, int(length/2)-1, -int(width/2)+1, -int(length/2)+1)


    if (monster_count == 1):
    	room += '<DrawEntity x="0" y="64" z="7" type="Sheep"/>'
    else:
    	room += '''
    			'''
    return room

def set_player_position():
	return