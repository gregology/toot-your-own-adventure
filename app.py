from story import Story
from mastodon import Mastodon
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--mastodon_server', type=str, default='clar.ke')
parser.add_argument('--mastodon_access_token', type=str)
parser.add_argument('--openai_api_key', type=str)
parser.add_argument('--openai_organization', type=str)
parser.add_argument('--genre', type=str)
parser.add_argument('--poll_character_limit', type=int, default=50)
parser.add_argument('--number_of_cues', type=int, default=3)
parser.add_argument('-c', '--cli', action='store_true', help='flag to run in cli mode (for testing)')
args = parser.parse_args()

print("\n########################\nToot your own adventure!\n########################\n")

story = Story(
    genre=args.genre,
    api_key=args.openai_api_key,
    organization=args.openai_organization,
    poll_character_limit=args.poll_character_limit,
    number_of_cues=args.number_of_cues
)

if args.cli:
    paragraphs = story.start()
    for i in range(100):
        print(story)
        story.prompt_to_continue()
    exit()

mastodon = Mastodon(access_token=args.mastodon_access_token, mastodon_server=args.mastodon_server)

# mastodon.is_last_poll_expired()

previous_paragraphs = mastodon.get_paragraphs_from_previous_polls()
cue = mastodon.get_winning_cue_from_last_poll()

story.append_previous_paragraphs(paragraphs=previous_paragraphs)
story.continue_with_cue(cue)
new_cues = story.get_cues()
status = story.generate_status(new_cues)
options = [cue["summary"] for cue in new_cues]
previous_poll_id = mastodon.last_poll['id']

print(story)
print(new_cues)
print(new_cues)

mastodon.post_poll(status=status, options=options, expires_in=3*60, previous_poll_id=previous_poll_id)
