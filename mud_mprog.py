
from mud_comms import send_message
from mud_shared import colourize
from mud_abilities import AbilityType


MPROG_TEXT = {
    3300: [
'"Ah, welcome, traveler, to Whisperwood Hollow," the wise old shaman greets you, their voice as calming as the rustle of leaves. They gesture for you to come closer, their eyes twinkling with gentle wisdom. "I am the keeper of ancient healing arts, a humble servant of nature\'s delicate balance."',
'The shaman picks up a small bundle of dried herbs, crushing them gently between their fingers. The air fills with a soothing aroma. "Here, we live in harmony with the natural world, learning from its rhythms and secrets. Our greatest gift is the art of healing - a gift I see potential for in you."'
'They reach out, placing a warm, weathered hand on your shoulder. "I will teach you the \'cure\' spell, young one. It is a fundamental incantation that calls upon the healing energies of the earth to mend wounds and soothe pain." The shaman\'s voice is like a soft melody, imbuing each word with care and importance.'
'"Watch closely," they continue, closing their eyes and chanting softly in an ancient tongue. A gentle light emanates from their hands, growing brighter with each word. "This spell will aid you in your journey, allowing you to heal both yourself and others. May it serve as a reminder of the sacred bond between all living things."'
'As the light fades, the shaman opens their eyes, smiling at you with a mix of pride and kindness. "Go forth with this knowledge, and remember that true strength comes from understanding and compassion. May the spirits of the forest guide and protect you."'
    ]
}





def mprog_shaman_cure(player):
    if player.character.abilities.has_ability("cure"):
        return False

    for i in range(len(MPROG_TEXT[3300])):
        send_message(player, colourize(MPROG_TEXT[3300][i] + "\n\n", "bright white"))
    player.character.abilities.learn_ability("cure", AbilityType.SPELL)
    send_message(player, colourize("You have learned the spell 'cure'!\n", "bright yellow"))
    return True

MPROG_ROOM_CHECK = {
    3304: mprog_shaman_cure
}


def mprog_room_check(player):
    if player.current_room.vnum in MPROG_ROOM_CHECK:
        return MPROG_ROOM_CHECK[player.current_room.vnum](player)
    

