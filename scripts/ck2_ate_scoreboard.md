# CK2 "After the End" (ATE Fan Fork) End-Game Legacy Scoreboard

ATE keeps CK2's vanilla score thresholds (engine-hardcoded, not moddable) but reskins all 15 dynasty slots with its own post-apocalyptic-America lore, via `localisation/000_vanilla_overrides.csv`.

| Score | Dynasty | Description |
|---|---|---|
| 100,000 | **House Talanque**, Emperors of California | Elton the Lawgiver, a philosopher who avenged his murdered lord, used Cetic philosophy to unite the warring states of California and end centuries of chaos. |
| 90,000 | **House Jacaranda**, Kings of Mexico | Rose from the streets of Mexico City to restore the Mexican Empire, universally recognized as a continuation of pre-Event Mexico. |
| 80,000 | **House Royall**, Emperors of the Holy Columbian Confederacy | Leonidas Royall united the warring Evangelical South against millenarian Postadventist zealots, founding an empire claiming succession to Old America. |
| 70,000 | **House Clinton**, Kings of Hudsonia | Ellis I Clinton marched north from Manhattan to reclaim New York State from the Occultist kingdom of New England, ruling the Hudson Valley for centuries. |
| 60,000 | **House Sully**, Kings of Moskitia | Founded by the legendary King Newman, said to have lived 300+ years; one of the oldest, most stable kingdoms in Central America. |
| 50,000 | **House Abbas**, rulers of Socal | Zakariyya I established Socal and codified Imamite (post-Event Islamic) doctrine; later overthrown by their own vassals, House Carmine. |
| 40,000 | **House Tlgunghung**, Kings of the Haida Tlagaang | Descended from the mythic King Yahguaas; united the Haida and spread the Raven Deluge faith across the Pacific Northwest. |
| 30,000 | **House Nokona**, Kings of Comancheria | Pahayoko I led the Comanche to reclaim their homeland in Texas, forming a stable feudal kingdom that endures to 2666. |
| 20,000 | **House Mahonic**, Kings of New England | Vincent Mahonic united the Occultist tribes of New England; his empire fractured after his assassination and his son's defeat at Saratoga Springs. |
| 15,000 | **House Castel** of Quebec | Queen Véronique briefly united an independent Quebec; her line didn't outlive her, but her descendants still hold minor titles. |
| 10,000 | **House Pitchstone**, Americanist kings of Dakota | Ned Pitchstone avenged a slain President and consolidated Americanist rule in the Midwest before a Sioux resurgence ended the dynasty. |
| 7,500 | **House Yoder** | United much of Pennsylvania under Deitsch rule; wiped out in a cycle of Americanist–Anabaptist violence following a childless king's murder. |
| 5,000 | **House Tagötöka**, High Chieftains of Northern Basin | Tavibo "The Holy"/"The Mad" briefly conquered eastern Oregon on a syncretic Cetic-Gaian-Mormon philosophy; his empire split among his heirs. |
| 2,000 | **House Soady** | The Viking raider Albert Soady sacked his way down the Mississippi and up the East Coast, sacrificing President Avondale, but his kingdom of Superior didn't survive him. |
| 1,000 | **House Avondale** | An influential Americanist dynasty that produced three Presidents over 200 years — ended violently when Albert Soady sacked Chicago and sacrificed the family. |

Source: [After the End Fan Fork — localisation/000_vanilla_overrides.csv](https://github.com/9Kbits/ateff/blob/master/After%20the%20End%20Fan%20Fork/localisation/000_vanilla_overrides.csv)

## CK3 port cross-reference

Checked which of these CK2 dynasty names still exist in the CK3 "After the End" mod's dynasty files (`common/dynasties/`, `localization/english/replace/dynasties/dynasty_names_l_english.yml`, and starting `history/` data). All 15 have a CK3 counterpart; three were renamed/re-romanized during the port:

| CK2 name | CK3 equivalent | Notes |
|---|---|---|
| House Yudkow | **House Talanque** (`house_california_talanque`) | Confirmed via `history/characters/00_ate_characters_table_generated_California.txt` — Elton the Lawgiver (same character) belongs to `house_california_talanque`. `dynn_Yudkow` still exists in CK3 as an unrelated dynasty. |
| House Sulley | **House Sully** (`dynn_Sully`) | Holds `k_miskito` (Moskitia) at game start, matching the lore. |
| House Tagátáka | **House Tagötöka** (`dynn_Tagotoka`) | Re-diacritized spelling, same dynasty. |

All other dynasties (Jacaranda, Royall, Clinton, Abbas, Tlgunghung, Nokona, Mahonic, Castel, Pitchstone, Yoder, Soady, Avondale) carry over with identical spelling in CK3.
