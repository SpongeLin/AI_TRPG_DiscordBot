

from ast import Dict


class Character:
    def __init__(self, name: str, hp: int):
        self.name = name
        self.hp = hp
        self.max_hp = hp

class FightManager:
    def __init__(self):
        self.character_list : list[Character] = []
        pass
    
    def damage(self, target: str, damage: int) -> Dict[str, str]:
        for character in self.character_list:
            if character.name == target:
                character.hp -= damage
                if character.hp <= 0:
                    return {"status": "dead", "result": f"{target} 死亡"}
                return {"status": "damage", "result": f"{target} 受到 {damage} 點傷害，剩餘血量 {character.hp}"}
        return {"status": "not_found", "result": f"{target} 不存在"}
    
    def get_character_status(self) -> str:
        status = ""
        for character in self.character_list:
            status += f"{character.name} 血量: {character.hp}/{character.max_hp}\n"
        return status
    
        
    
fight_manager = FightManager()





