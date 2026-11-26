"""Scenario variants: same characters, different scenes every game and every day.

Each visitor keeps its base card as scenario 0, plus the variants below. For each game the code shuffles
the scenarios per visitor (seeded), then steps through them day by day, so a character never repeats
yesterday's scene and no two games play out in the same order.

Variants only change the STORY fields (goal, secret, sample_line, ...). Numbers such as max_bribe,
opening_offer, ask and the stat effects stay on the base card, so the game code still owns the economy.
Everything here is fictional satire; no real people, parties, companies or places.
"""

import contextvars
import random
from dataclasses import replace

STORY_FIELDS = {"goal", "secret", "personality", "voice", "sample_line", "if_refused", "remembers"}


def _v(goal, line, **kw):
    return {"goal": goal, "sample_line": line, **kw}


VARIANTS = {
    "don_ramon": [
        _v("Rezoning of the Pogi Bay shoreline so he can reclaim land for a 40-floor condo tower.",
           "Mayor! Tingnan mo 'tong maquette. Pogi Bay Residences, kwarenta palapag. [slides a brown envelope] Pang-merienda lang 'yan.",
           secret="None. Just greedy. He already sold sixty units before any permit existed."),
        _v("A fast-track permit for his 'Pogi Bay Fish Port', which is mostly a parking lot for a mall.",
           "Mayor ko, para sa mga mangingisda 'to, pramis! Fish port! Konting commercial space lang sa ibabaw. [slides a brown envelope]"),
        _v("Make the inspection of his half-built Pogi Bay tower 'quietly pass' after a crack appeared on the third floor.",
           "Mayor, maliit na bitak lang 'yon, parang buhok. Sayang naman kung ma-delay ang buong tower. [slides a brown envelope]",
           secret="The crack is not small. He knows it."),
    ],
    "lola_rosing": [
        _v("A footbridge for Barangay Lubog, because her grandchildren wade through a flooded creek to reach school.",
           "Magandang umaga po, Mayor. Yung mga apo ko po, lumulusong sa baha papunta sa eskwela. Tulay lang po sana, kahit maliit."),
        _v("Her late husband's veteran pension, stuck at the city hall counter for two years under a 'lost form'.",
           "Mayor, nawala raw po yung form ng asawa ko. Dalawang taon na po akong pabalik-balik. Baka po matulungan ninyo ako."),
        _v("Medicine money for the barangay's dialysis patients after the city clinic ran out of stock.",
           "Mayor, wala na raw po stock sa city clinic. Yung kapitbahay po naming nagda-dialysis, hindi na makabili. Baka po may mailaan kayo."),
    ],
    "ms_reyes": [
        _v("Ask the mayor about the 'ghost employees' on the city payroll.",
           "Good morning, Mayor! Quick one lang for 'Pogi Ngayon'. May nakita po kaming pangalan sa payroll na walang opisina. Kilala po ba ninyo si 'Ruben Dela Cerna'?",
           secret="She already has one name on the list and wants to see if the mayor flinches."),
        _v("Get an on-air birthday greeting from the mayor, then slip in a question about where the relief funds went.",
           "Mayor, birthday po ng station manager namin! Pa-greet naman po sa 'Pogi Ngayon'. Ay, tsaka, saan po napunta yung relief fund?"),
        _v("Interview the mayor about the 'brown envelope' rumors going around the city hall canteen.",
           "Mayor, pasensya na po, may tsismis po sa canteen. Totoo po bang may mga sobre dito tuwing Biyernes?"),
    ],
    "engr_santos": [
        _v("Win the plaza repainting and 'beautification' contract for Santos Builders.",
           "Good afternoon po, Mayor. Para po sa plaza. May 'standard arrangement' po ba kayo dito sa mga beautification projects?"),
        _v("Win the public market roof repair contract for Santos Builders.",
           "Mayor, good morning po. Yung bubong po ng palengke, butas-butas na. Pwede pong kami na... ano po ba ang usual na proseso?"),
        _v("Win the city street-lighting contract for Santos Builders.",
           "Good afternoon po, Mayor. Street lights po, Santos Builders. Ano po ba ang pwedeng... arrangement para sa ganitong proyekto?"),
    ],
    "kuya_boy": [
        _v("A raise to stay quiet. His price is ₱50,000, and he has a long list of reasons.",
           "Boss, kumusta ang umaga? Nga pala, tumaas na naman ang bigas. Tumaas din ba ang sweldo ko? Hehe. Hindi joke."),
        _v("A raise, plus a 'consultant' title for his cousin. His price is ₱50,000 and the title is free.",
           "Boss, may pinsan ako, magaling sa computer. Consultant sana. Tapos yung raise ko, siyempre. Alam mo na."),
        _v("Help with his daughter's graduation, which he calls the mayor's moral duty. His price is ₱50,000.",
           "Boss, gagraduate na si Bea. Hindi ko kayang bayaran lahat. Pero alam mo rin namang marami akong alam."),
    ],
    "boss_erning": [
        _v("The contract to supply hollow blocks and cement for every city school repair, with the usual 'SOP'.",
           "Mayor! School repairs po, kami na sa hollow blocks. Standard lang po, SOP. Kayo po bahala sa percentage."),
        _v("The relief-goods packing contract, with the usual 'SOP', because 'bagyo na naman'.",
           "Mayor, bago pa bumagyo, ayusin na natin ang relief packs. Softdrinks included po! SOP lang, kayo po bahala."),
        _v("A monthly drainage declogging contract, with the usual 'SOP'. He insists the canals clog every month.",
           "Mayor, barado na naman ang kanal. Monthly po tayo mag-declog para sure. SOP, standard lang, kayo po bahala."),
    ],
    "kap_luz": [
        _v("Release the ₱300,000 fund for the barangay covered-court roof, split 50/50 with the mayor.",
           "Mayor, pirma na lang po para sa bubong ng court. Hati na lang tayo, para fair. May picture pa, bago pa yung bubong.",
           secret="The roof was never built. She sold the old tin sheets."),
        _v("Release the ₱300,000 fund for the barangay anti-dengue fogging program, split 50/50 with the mayor.",
           "Mayor, mabilis lang 'to ha, may meeting pa 'ko. Fogging po, ₱300,000. Hati na lang tayo, para fair.",
           secret="The fogging truck broke down in March and she hasn't told anyone."),
        _v("Release the ₱300,000 fund for a barangay livelihood training, split 50/50 with the mayor.",
           "Mayor, livelihood training po, may attendance sheet pa. Pirma na lang po. Hati tayo, ha?",
           secret="The 'trainees' are her relatives, and the training was a picnic."),
    ],
    "atty_villaflor": [
        _v("Ask about the purchase of 200 ballpens that cost ₱5,000 each.",
           "Good morning, Mayor. Courtesy visit lang po. May ilang tanong ako tungkol sa 200 ballpens na ₱5,000 bawat isa. Siguro po, magandang ballpen."),
        _v("Verify the signatures on the 'completed' Barangay Lubog health center papers.",
           "Mayor, nagpunta po ako sa Lubog kahapon. Karatula lang po ang nakita ko. Baka po may paliwanag kayo?"),
        _v("Ask about 'consulting fees' paid to a company with exactly one employee.",
           "Good morning, Mayor. Napansin ko po ang 'consulting fees' sa isang kumpanyang isa lang ang empleyado. Coincidence po siguro?"),
    ],
    "sir_jepoy": [
        _v("Get paid for a 'Mayor vs. Street Food' challenge video, plus a 'Chief Eater' title.",
           "Hello mga ka-Pogi! Mayor, collab tayo! Mayor vs. Street Food! Viral 'to, promise. Pero syempre, may talent fee."),
        _v("Get paid for a 'Mayor Reacts to Hate Comments' video, plus a 'Digital Ambassador' title.",
           "Mayor! Reaction video tayo sa mga hate comments mo! Grabe ang views nito, not clickbait. Pero may talent fee, ha."),
        _v("Get paid to livestream the mayor's 'surprise inspection' of the public market.",
           "Mayor, live tayo sa palengke! Surprise inspection, parang walang script. Pero may script, syempre. Talent fee lang."),
    ],
    "nanay_merly": [
        _v("A guarantee letter so the hospital will operate on her husband. She has been to four offices this week.",
           "Mayor, pasensya na po. Pang-apat na opisina ko na po ito. Yung asawa ko po, kailangan operahan. Guarantee letter lang po sana."),
        _v("Burial assistance for her father, whom the family cannot afford to bury. She is too proud to ask twice.",
           "Mayor, pasensya na po. Namatay po yung tatay ko kahapon. Hindi po namin kayang ipalibing. Baka po may burial assistance."),
        _v("School fee help so her son can take the board-exam review. She cleans offices at night.",
           "Mayor, pasensya na po sa abala. Yung anak ko po, gusto pong mag-review para sa board exam. Hindi na po kaya ng sweldo ko."),
    ],
    "vm_ging": [
        _v("Get Junjun the exclusive contract to build the city 'tourism app', which has no budget yet.",
           "Mayor, nagdala ako ng pansit! Si Junjun nga pala, magaling sa apps. Gagawa siya ng tourism app. Wala pang pondo, pero maganda ang pangalan."),
        _v("Get herself named chair of the city anniversary committee, which controls the gala budget.",
           "Mayor, kain ka muna, anak. Ay, by the way, sino po kaya ang mamumuno sa anniversary committee? Ako na lang siguro, para di ka mapagod."),
        _v("Get her cousin's catering business 'considered' for every city event. She already told him it's done.",
           "Mayor, may dala akong pansit. Yung pinsan ko nga pala, caterer. Sinabi ko na sa kanya na siya na. Ay, naku, na-excite lang ako."),
    ],
    "carlo": [
        _v("The Christmas gala catering and lights contract.",
           "{uncle_aunt} Mayor! So like, para sa Christmas gala, kami na sa catering and lights. Family discount pa, and syempre may balik sa 'yo."),
        _v("The city ID-card printing contract.",
           "{uncle_aunt} Mayor, so like, ID cards? Printer lang kailangan namin. Super easy. May balik pa sa 'yo."),
        _v("A 'social media consultancy' for the fiesta, which is mostly him posting selfies.",
           "{uncle_aunt} Mayor! So like, ako na bahala sa fiesta socmed. May aesthetic ako, promise. May consultancy fee lang."),
    ],
}


def _more(cid, *variants):
    VARIANTS[cid] += list(variants)


_more("don_ramon",
      _v("A 'temporary' permit for a night market on the old fish port, which he plans to turn into mall parking.",
         "Mayor ko! Night market lang, pang-masa! Temporary lang 'yan, promise. [slides a brown envelope] Pang-merienda."),
      _v("Get the city to buy his unsold condo units as 'housing for employees' at triple the price.",
         "Mayor, para sa mga empleyado ng city hall 'to! Presyong kaibigan. Triple lang. [slides a brown envelope]"))
_more("lola_rosing",
      _v("A streetlight for her corner of Barangay Lubog, because her granddaughter walks home in the dark.",
         "Mayor, magandang umaga po. Yung apo ko po, naglalakad pauwi sa dilim. Isang poste lang po ng ilaw sana."),
      _v("Free vaccines for the barangay's children, which the health center keeps running out of.",
         "Mayor, wala na naman daw pong bakuna sa health center. Yung mga bata po, nakapila na naman. Baka po matulungan ninyo kami."))
_more("ms_reyes",
      _v("Ask the mayor to explain 25 'smart' trash bins that nobody can find.",
         "Mayor, quick one lang po. Yung bente-singkong smart trash bins, nasaan po? Hindi pa namin nakita sa kahit anong kanto."),
      _v("Ask for a 'day in the life' feature, then slip in a question about the pamangkin's brand-new company.",
         "Mayor, feature po sana kayo sa 'Pogi Ngayon'. Ay, tsaka, totoo po bang kababago lang ng kumpanya ng pamangkin ninyo?"))
_more("engr_santos",
      _v("Win the bid to repair the city hall roof, which leaks directly over the mayor's desk.",
         "Good afternoon po, Mayor. Napansin ko pong may tulo sa taas ng mesa ninyo. Pwede po ba naming ayusin... under the usual terms?"),
      _v("Win the contract to build public toilets at the bus terminal.",
         "Mayor, good morning po. Public CR po sa terminal. Ano po ang usual na proseso para sa ganitong proyekto?"))
_more("kuya_boy",
      _v("A raise, plus a company motorcycle. His price is ₱50,000, and the motorcycle is negotiable.",
         "Boss, ang layo ng bahay ko. Bigyan mo naman ako ng motor. At yung raise, siyempre. Alam mo na."),
      _v("A raise, because he has been covering for the mayor and wants it recognized. His price is ₱50,000.",
         "Boss, ilang beses ko nang sinabing 'wala po siya' kapag hinahanap ka. Napapagod na 'ko magsinungaling. May bayad ang katahimikan, Boss."))
_more("boss_erning",
      _v("The contract for 500 plastic monobloc chairs for city events, with the usual 'SOP'.",
         "Mayor! Monobloc chairs po, limang daan. Standard lang po, SOP. Kayo po bahala."),
      _v("The city fiesta lighting and banderitas contract, with the usual 'SOP'.",
         "Mayor, para sa fiesta! Banderitas at ilaw. SOP lang, kayo po bahala sa percentage."))
_more("kap_luz",
      _v("Release the ₱300,000 fund for barangay tanod uniforms, split 50/50 with the mayor.",
         "Mayor, uniform po ng tanod. Pirma na lang. Hati na lang tayo, para fair.",
         secret="The tanods already have uniforms. She ordered a second set for her relatives."),
      _v("Release the ₱300,000 fund for solar streetlights, split 50/50 with the mayor.",
         "Mayor, solar streetlights po. Maliwanag na maliwanag na sa Lubog. Hati tayo, ha.",
         secret="Only two lamps were installed, and one of them is her own gate light."))
_more("carlo",
      _v("The city's school-uniform supply contract.",
         "{uncle_aunt} Mayor! So like, uniform for all public schools? Super kaya namin. May balik pa sa 'yo."),
      _v("A 'Welcome to Pogi City' arch at the city entrance.",
         "{uncle_aunt} Mayor, so like, welcome arch? Super iconic. Ako na bahala sa design, may balik sa 'yo."))

# Twists: a small mood or situation added to a visitor's personality, chosen per visitor per day.
# They never touch money or stats, so the same scenario still plays differently every time.
TWISTS = [
    "Today you are in a visible hurry and keep glancing at your phone.",
    "Today you brought a small pasalubong (a box of pastries) and mention it once.",
    "Today you are nervous because you heard a reporter is somewhere in the building.",
    "Today you open with a short story about something odd on the way to city hall (a flooded street, a stray dog, a broken traffic light).",
    "Today you ask about the mayor's family and health before getting to the point.",
    "Today you speak almost entirely in Tagalog, with only a few English words.",
    "Today you are celebrating something (a birthday, a new baby, a promotion) and mention it once.",
    "Today you are unusually patient, but you will not leave without a clear answer.",
    "Today you lose patience quickly: if the mayor stalls twice, you say so plainly and leave.",
    "Today you quote an invented 'sabi ng matatanda' proverb to make your point.",
    "Today you are wearing something unusual (a loud shirt, a barong two sizes too big) and joke about it once.",
    "Today you are coughing from the dusty roads and mention the road conditions once.",
    "Today you have a relative named Tonton with you who stays quiet in the corner; mention him once.",
    "Today you are extra polite and call the mayor by title every time.",
]

for _id, _opts in VARIANTS.items():       # catch typos early: variants may only touch story fields
    for _o in _opts:
        assert set(_o) <= STORY_FIELDS, (_id, set(_o) - STORY_FIELDS)

_CTX = contextvars.ContextVar("scene_ctx", default=(0, 1, {}))


def set_scene_context(seed: int, day: int, visits: dict | None = None) -> None:
    """Call at the top of every script run: this game's seed, the current day, and the visit counts."""
    _CTX.set((seed, day, visits if visits is not None else {}))


def scene_index(card_id: str, n: int, seed: int, visit_no: int) -> int:
    """Index into [base card] + variants. Shuffled per game and visitor; each visit steps to the next scene."""
    order = list(range(n))
    random.Random(f"{seed}:{card_id}").shuffle(order)
    return order[(visit_no - 1) % n]


def scene_card(card):
    """The card as it plays today: this visit's scenario plus today's twist. Event cards are unchanged."""
    seed, day, visits = _CTX.get()
    fields = {}
    options = VARIANTS.get(card.id)
    if options:
        i = scene_index(card.id, len(options) + 1, seed, max(1, visits.get(card.id, 1)))
        if i:
            fields.update(options[i - 1])
    if card.kind == "visitor":
        twist = random.Random(f"{seed}:{card.id}:{day}:twist").choice(TWISTS)
        fields["personality"] = f"{fields.get('personality', card.personality)} {twist}"
    return replace(card, **fields) if fields else card