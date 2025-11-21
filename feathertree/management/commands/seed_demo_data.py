from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from feathertree.models import Story, Chapter


class Command(BaseCommand):
    help = "Seed the database with demo Stories and Chapters"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete existing demo data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        # Wipe data if requested
        if options["fresh"]:
            self.stdout.write(self.style.WARNING("Deleting existing Stories and Chapters..."))
            Chapter.objects.all().delete()
            Story.objects.all().delete()

        if Story.objects.exists() and not options["fresh"]:
            self.stdout.write(self.style.WARNING(
                "Stories already exist. Use --fresh to reset demo data."
            ))
            return

        self.stdout.write("Creating demo users...")

        # email, display_name, is_restricted
        demo_users = [
            ("alice@example.com", "Alice", False),
            ("bob@example.com", "Bob", False),
            ("captain@example.com", "Captain", False),
            ("dana@example.com", "Aana", False),
            ("eli@example.com", "Eli", True),
        ]

        authors = []
        for email, display_name, is_restricted in demo_users:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "display_name": display_name,
                    "is_restricted": is_restricted,
                },
            )
            # Backfill display_name if user existed without it
            if not getattr(user, "display_name", None):
                user.display_name = display_name
                user.save(update_fields=["display_name"])
            authors.append(user)

        author1, author2, author3, author4, author5 = authors

        # Set passwords if needed
        for user in authors:
            if not user.has_usable_password():
                user.set_password("password123")
                user.save()

        self.stdout.write("Creating demo stories and chapters...")

        # --------------------------------------
        # STORY 1: Weaving Wood Lighthouse
        # --------------------------------------
        story1 = Story.objects.create(title="The Lighthouse")

        prev = None
        created_s1 = []
        chapters_story1 = [
            {
                "ordinal": 1,
                "title": "A Stranger on the Road",
                "content": "The sun dipped low as the stranger approached the small town gate...",
                "author": author1,
            },
            {
                "ordinal": 2,
                "title": "Voices Under the Big Top",
                "content": "The circus tents loomed like bright mushrooms along the roadside...",
                "author": author2,
            },
            {
                "ordinal": 3,
                "title": "Secrets in the Sawdust",
                "content": "Backstage, whispers of stars, eclipses, and old gods grew louder...",
                "author": author3,
            },
        ]
        for data in chapters_story1:
            prev = Chapter.objects.create(
                ordinal=data["ordinal"],
                title=data["title"],
                content=data["content"],
                draft=False,
                submitted_for_review=False,
                story=story1,
                author=data["author"],
                previous_chapter=prev,
            )
            created_s1.append(prev)

        # Extra branches for STORY 1 (ordinals 2 and 3)
        s1_ch1 = created_s1[0]        # ordinal 1
        s1_ch2_main = created_s1[1]   # ordinal 2

        # Additional ordinal 2 chapters (store them so we can hang 3's off each)
        s1_ch2_fork = Chapter.objects.create(
            ordinal=2,
            title="Fork in the Fairway",
            content=(
                "Instead of following the stranger, the party slipped toward a side tent where "
                "shadowy figures traced constellations in spilled ale."
            ),
            draft=False,
            submitted_for_review=False,
            story=story1,
            author=author3,
            previous_chapter=s1_ch1,
        )
        s1_ch2_whispers = Chapter.objects.create(
            ordinal=2,
            title="Whispers at the Wagon",
            content=(
                "A quiet conversation at the back of a supply wagon hinted that the circus "
                "had one extra wagon no one admitted owning."
            ),
            draft=False,
            submitted_for_review=False,
            story=story1,
            author=author4,
            previous_chapter=s1_ch1,
        )
        s1_ch2_midnight = Chapter.objects.create(
            ordinal=2,
            title="The Midnight Drum",
            content=(
                "A deep drumbeat thudded from the far end of the fairgrounds, slow and steady like a heartbeat. "
                "Performers froze mid-step, glancing toward the darkness as if the sound marked the arrival of someone "
                "they hoped would never return."
            ),
            draft=False,
            submitted_for_review=False,
            story=story1,
            author=author5,
            previous_chapter=s1_ch1,
        )

        # Additional ordinal 3 chapters (existing, coming off the main 2)
        Chapter.objects.create(
            ordinal=3,
            title="The Star-Scarred Map",
            content=(
                "Hidden beneath a loose floorboard, they found a map inked with tiny stars, "
                "each one marking a town where the circus had vanished overnight."
            ),
            draft=False,
            submitted_for_review=False,
            story=story1,
            author=author2,
            previous_chapter=s1_ch2_main,
        )
        Chapter.objects.create(
            ordinal=3,
            title="A Promise in Candlelight",
            content=(
                "By candlelight, the ringmaster swore the show must go on, even as the wind "
                "outside carried the scent of rain and prophecy."
            ),
            draft=False,
            submitted_for_review=False,
            story=story1,
            author=author4,
            previous_chapter=s1_ch2_main,
        )

        # NEW: ensure every chapter 2 has at least one chapter 3 child
        Chapter.objects.create(
            ordinal=3,
            title="Road of Lanterns",
            content=(
                "Following the side tent’s path, the party found a row of paper lanterns leading away "
                "from the fairgrounds and into the trees, each one painted with a different crescent moon."
            ),
            draft=False,
            submitted_for_review=False,
            story=story1,
            author=author1,
            previous_chapter=s1_ch2_fork,
        )
        Chapter.objects.create(
            ordinal=3,
            title="Secrets Behind the Canvas",
            content=(
                "Behind the supply wagon’s canvas, an old ledger listed names and dates—but the last page "
                "had been ripped clean out, leaving only the impression of a signature."
            ),
            draft=False,
            submitted_for_review=False,
            story=story1,
            author=author5,
            previous_chapter=s1_ch2_whispers,
        )
        Chapter.objects.create(
            ordinal=3,
            title="The Drum’s Echo",
            content=(
                "When the drumbeat stopped, the silence felt heavier than sound. In its wake, the party heard "
                "a single child’s laugh coming from the empty performance ring."
            ),
            draft=False,
            submitted_for_review=False,
            story=story1,
            author=author3,
            previous_chapter=s1_ch2_midnight,
        )

        # --------------------------------------
        # STORY 2: Eddie the Food Cart Vendor
        # --------------------------------------
        story2 = Story.objects.create(title="Food Cart of Fortune")

        prev = None
        created_s2 = []
        chapters_story2 = [
            {
                "ordinal": 1,
                "title": "The Park Bench Incident",
                "content": "Eddie wiped sweat from his brow as the New Orleans summer clung to his shirt...",
                "author": author2,
            },
            {
                "ordinal": 2,
                "title": "Mystery Customer",
                "content": "He almost missed the man in the linen suit who ordered three hot dogs and left no name...",
                "author": author3,
            },
            {
                "ordinal": 3,
                "title": "Opportunity in Disguise",
                "content": "By the time Eddie saw his cart on the evening news, he was already asleep.",
                "author": author4,
            },
        ]
        for data in chapters_story2:
            prev = Chapter.objects.create(
                ordinal=data["ordinal"],
                title=data["title"],
                content=data["content"],
                draft=False,
                submitted_for_review=False,
                story=story2,
                author=data["author"],
                previous_chapter=prev,
            )
            created_s2.append(prev)

        # Extra branches for STORY 2 (ordinals 2 and 3)
        s2_ch1 = created_s2[0]
        s2_ch2_main = created_s2[1]

        # Additional ordinal 2 chapters (capture them)
        s2_ch2_blogger = Chapter.objects.create(
            ordinal=2,
            title="The Blogger with a Camera",
            content=(
                "A food blogger with an old film camera snapped three quick photos of the cart, "
                "muttering about 'authentic street hustle'."
            ),
            draft=False,
            submitted_for_review=False,
            story=story2,
            author=author5,
            previous_chapter=s2_ch1,
        )
        s2_ch2_couple = Chapter.objects.create(
            ordinal=2,
            title="The Couple from Uptown",
            content=(
                "A laughing couple from Uptown tried the special, promised to 'tell everyone at the office,' "
                "and left a business card Eddie forgot to read."
            ),
            draft=False,
            submitted_for_review=False,
            story=story2,
            author=author1,
            previous_chapter=s2_ch1,
        )

        # Additional ordinal 3 chapters (existing, off main 2)
        Chapter.objects.create(
            ordinal=3,
            title="Viral by Morning",
            content=(
                "By sunrise, the blogger’s post had gone viral. Eddie’s cart, crooked umbrella and all, "
                "was now the backdrop of a city-wide craving."
            ),
            draft=False,
            submitted_for_review=False,
            story=story2,
            author=author3,
            previous_chapter=s2_ch2_main,
        )
        Chapter.objects.create(
            ordinal=3,
            title="A Call from Downtown",
            content=(
                "His phone buzzed with a number he didn’t recognize. Someone from Downtown wanted to talk "
                "about a partnership, something about 'brand synergy' and a food truck fleet."
            ),
            draft=False,
            submitted_for_review=False,
            story=story2,
            author=author1,
            previous_chapter=s2_ch2_main,
        )
        Chapter.objects.create(
            ordinal=3,
            title="The Festival Invitation",
            content=(
                "Buried under spam and discount codes, Eddie finally noticed an email with the subject line "
                "'Featured Vendor Opportunity.' The city’s summer food festival wanted his cart at center stage, "
                "sandwiched between gourmet trucks with marketing budgets bigger than his yearly income."
            ),
            draft=False,
            submitted_for_review=False,
            story=story2,
            author=author4,
            previous_chapter=s2_ch2_main,
        )

        # NEW: chapter 3 children for the two extra chapter 2s
        Chapter.objects.create(
            ordinal=3,
            title="Review of the Century",
            content=(
                "The blogger’s review called Eddie’s food 'recklessly honest comfort,' and the comments filled with "
                "locals arguing about whether the price was still too low."
            ),
            draft=False,
            submitted_for_review=False,
            story=story2,
            author=author2,
            previous_chapter=s2_ch2_blogger,
        )
        Chapter.objects.create(
            ordinal=3,
            title="Missed Call, Missed Chance?",
            content=(
                "Later that night, Eddie found the Uptown couple’s voicemail. They weren’t just office workers—they owned "
                "a tiny investment firm looking for 'the next big street food brand.'"
            ),
            draft=False,
            submitted_for_review=False,
            story=story2,
            author=author5,
            previous_chapter=s2_ch2_couple,
        )

        # --------------------------------------
        # STORY 3: Ghost Ship
        # --------------------------------------
        story3 = Story.objects.create(title="The Phantom of the Midnight Tide")

        prev = None
        created_s3 = []
        chapters_ghost = [
            {
                "ordinal": 1,
                "title": "The Lantern’s Glow",
                "content": (
                    "Jonas had fished the coast for twenty years, but he had never seen a light like that—"
                    "a pale green lantern bobbing on a vessel no one claimed to own. "
                    "Rumor said the Midnight Tide only appeared to those marked by fate."
                ),
                "author": author3,
            },
            {
                "ordinal": 2,
                "title": "Voices in the Fog",
                "content": (
                    "As Jonas drew closer, the fog thickened into ropes of silver mist. "
                    "He heard whispers—pleading, desperate, echoing from wood that should not float. "
                    "The ship’s hull gleamed like wet bone."
                ),
                "author": author3,
            },
            {
                "ordinal": 3,
                "title": "The Captain’s Warning",
                "content": (
                    "A figure emerged from the bow: translucent, solemn, and dressed in an officer’s coat "
                    "from a century long past. “Turn back,” the ghostly captain said. "
                    "“For those who board the Midnight Tide never return the same.”"
                ),
                "author": author5,
            },
        ]
        for data in chapters_ghost:
            prev = Chapter.objects.create(
                ordinal=data["ordinal"],
                title=data["title"],
                content=data["content"],
                draft=False,
                submitted_for_review=False,
                story=story3,
                author=data["author"],
                previous_chapter=prev,
            )
            created_s3.append(prev)

        # Extra branches for STORY 3 (ordinals 2 and 3)
        s3_ch1 = created_s3[0]
        s3_ch2_main = created_s3[1]

        # Additional ordinal 2 chapters (capture)
        s3_ch2_nets = Chapter.objects.create(
            ordinal=2,
            title="The Nets That Came Back Empty",
            content=(
                "Every net Jonas cast near the spectral hull came back empty, as if the sea itself "
                "refused to give up its dead."
            ),
            draft=False,
            submitted_for_review=False,
            story=story3,
            author=author4,
            previous_chapter=s3_ch1,
        )
        s3_ch2_echoes = Chapter.objects.create(
            ordinal=2,
            title="Echoes on the Waves",
            content=(
                "The creak of phantom rigging echoed across the water, each groan of timber "
                "matching the rhythm of a heartbeat that was not his own."
            ),
            draft=False,
            submitted_for_review=False,
            story=story3,
            author=author1,
            previous_chapter=s3_ch1,
        )

        # Additional ordinal 3 chapters (existing)
        Chapter.objects.create(
            ordinal=3,
            title="Bargain of the Drowned",
            content=(
                "The captain spoke of a bargain: safe passage through an oncoming storm in exchange "
                "for a single memory Jonas would never reclaim."
            ),
            draft=False,
            submitted_for_review=False,
            story=story3,
            author=author3,
            previous_chapter=s3_ch2_main,
        )
        Chapter.objects.create(
            ordinal=3,
            title="Names on the Tide",
            content=(
                "Names of the lost rolled with the waves, each syllable clinging to the fog until "
                "Jonas heard his own whispered back to him."
            ),
            draft=False,
            submitted_for_review=False,
            story=story3,
            author=author2,
            previous_chapter=s3_ch2_main,
        )

        # NEW: chapter 3 children for the two extra chapter 2s
        Chapter.objects.create(
            ordinal=3,
            title="The Catch That Wasn’t",
            content=(
                "One net finally came back heavy, but inside there were only barnacle-crusted trinkets—rings, lockets, "
                "and a rusted compass still spinning."
            ),
            draft=False,
            submitted_for_review=False,
            story=story3,
            author=author5,
            previous_chapter=s3_ch2_nets,
        )
        Chapter.objects.create(
            ordinal=3,
            title="Heartbeat of the Hull",
            content=(
                "Pressing his palm to the ghostly hull, Jonas felt a steady thump—like a heart buried inside the wood, "
                "beating in time with the incoming tide."
            ),
            draft=False,
            submitted_for_review=False,
            story=story3,
            author=author4,
            previous_chapter=s3_ch2_echoes,
        )

        # --------------------------------------
        # STORY 4: NYC Noir Crime Drama
        # --------------------------------------
        story4 = Story.objects.create(title="Cigarettes on Seventh Avenue")

        prev = None
        created_s4 = []
        chapters_noir = [
            {
                "ordinal": 1,
                "title": "Rain on Neon",
                "content": (
                    "The rain came down in sheets, turning Seventh Avenue into a river of smeared neon. "
                    "Detective Mara Vale lit a cigarette beneath the awning of a 24-hour diner, watching "
                    "the crime scene tape flutter like tired flags in the wind."
                ),
                "author": author1,
            },
            {
                "ordinal": 2,
                "title": "A Body in the Alley",
                "content": (
                    "The vic lay face-up in the narrow alley, eyes open, reflecting a broken slice of the city skyline. "
                    "No wallet, no phone, just a matchbook from a jazz club in Harlem and a single chess piece "
                    "pressed into his palm: a black knight."
                ),
                "author": author2,
            },
            {
                "ordinal": 3,
                "title": "The Club Called Checkmate",
                "content": (
                    "The Checkmate was the kind of place where the piano never stopped and the regulars never talked to cops. "
                    "Mara stepped into the haze of cigarette smoke and trumpet notes, flashing her badge just long enough "
                    "to make everyone uncomfortable. On stage, the singer’s eyes lingered on Mara a second too long."
                ),
                "author": author4,
            },
        ]
        for data in chapters_noir:
            prev_ch = Chapter.objects.create(
                ordinal=data["ordinal"],
                title=data["title"],
                content=data["content"],
                draft=False,
                submitted_for_review=False,
                story=story4,
                author=data["author"],
                previous_chapter=prev,
            )
            created_s4.append(prev_ch)
            prev = prev_ch

        # Base chapter references
        s4_ch1 = created_s4[0]
        s4_ch2_main = created_s4[1]
        s4_ch3_main = created_s4[2]

        # Additional ordinal 2 (branches, captured)
        s4_ch2_coffee = Chapter.objects.create(
            ordinal=2,
            title="Coffee and Interrogations",
            content=(
                "Back at the precinct, Mara stared at the evidence board while cold coffee grew bitter. "
                'Every thread she pinned traced back to a whisper: "Checkmate wasn’t always a club."'
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author3,
            previous_chapter=s4_ch1,
        )
        s4_ch2_trench = Chapter.objects.create(
            ordinal=2,
            title="The Man in the Trench Coat",
            content=(
                "A man in a gray trench coat lingered on the subway platform, hat brim low, as if he'd seen "
                "all this before and already memorized the ending."
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author5,
            previous_chapter=s4_ch1,
        )

        # Additional ordinal 3 (branches off main 2)
        Chapter.objects.create(
            ordinal=3,
            title="Off-the-Record",
            content=(
                "In a back booth at the Checkmate, Mara slid her badge away and asked the singer to level with her. "
                "The truth came in fragments and metaphors, half-shaded like the club itself."
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author2,
            previous_chapter=s4_ch2_main,
        )
        Chapter.objects.create(
            ordinal=3,
            title="The Knight’s Gambit",
            content=(
                "Another knight chess piece appeared on her desk the next morning. This one was carved from ebony wood. "
                "The note pinned beneath it simply read: 'Two moves left.'"
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author4,
            previous_chapter=s4_ch2_main,
        )

        # NEW: chapter 3 children for the two extra chapter 2s
        Chapter.objects.create(
            ordinal=3,
            title="Confession Over Cold Coffee",
            content=(
                "Hours into her interrogation marathon, a low-level informant finally cracked, admitting that the alley "
                "victim had once worked security at the Checkmate before it 'changed ownership'."
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author1,
            previous_chapter=s4_ch2_coffee,
        )
        Chapter.objects.create(
            ordinal=3,
            title="Platform Standoff",
            content=(
                "On the subway platform, Mara called out to the man in the trench coat. He paused, one foot over the yellow line, "
                "and asked if she was ready to lose more than just sleep over this case."
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author3,
            previous_chapter=s4_ch2_trench,
        )

        # --------------------------------------
        # ORDINAL 4 AND 5 EXTENSION (DEEP BRANCHING)
        # --------------------------------------

        # One main ordinal 4 chapter branching from the ordinal 3 main path
        s4_ch4_main = Chapter.objects.create(
            ordinal=4,
            title="The Basement Files",
            content=(
                "Deep beneath the precinct, Mara pulled old evidence boxes from a storage cage labeled 1973. "
                "Inside one folder lay a faded photograph of the Checkmate club—before the fire, before the murder, "
                "before the city tried to forget."
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author1,
            previous_chapter=s4_ch3_main,
        )

        # Three ordinal 5 branches off that chapter 4
        Chapter.objects.create(
            ordinal=5,
            title="The Photograph's Shadow",
            content=(
                "Mara flipped the photo over. A name was scrawled on the back: 'Vale.' "
                "Her own surname, written decades before she was born."
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author3,
            previous_chapter=s4_ch4_main,
        )
        Chapter.objects.create(
            ordinal=5,
            title="A Fire That Never Ended",
            content=(
                "The old reports described a fire that gutted the Checkmate, but witnesses claimed flames burned cold, "
                "like blue neon ice. Someone had erased most of the case file."
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author5,
            previous_chapter=s4_ch4_main,
        )
        Chapter.objects.create(
            ordinal=5,
            title="City Hall's Secret",
            content=(
                "Tucked in the box was a sealed letter from City Hall marked 'Eyes Only.' "
                "Inside was a single sentence: 'The Knight will fall when the singer remembers.'"
            ),
            draft=False,
            submitted_for_review=False,
            story=story4,
            author=author2,
            previous_chapter=s4_ch4_main,
        )

        self.stdout.write(self.style.SUCCESS("All demo stories with extra branches created successfully!"))
