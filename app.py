from story import Story
from mastodon import Mastodon
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--mastodon_server', type=str, help='server domain, for instance "mastodon.social"')
parser.add_argument('--mastodon_access_token', type=str, help='Mastodon access token, create one in Preferences -> Development -> New Application')
parser.add_argument('--openai_api_key', type=str, help='OpenAI api_key, https://platform.openai.com/account/api-keys', required=True)
parser.add_argument('--openai_organization', type=str, help='OpenAI organization, https://platform.openai.com/account/api-keys', required=True)
parser.add_argument('--genre', type=str, help='genre of the story, thriller, romance, sci-fi, etc.', default='sci-fi')
parser.add_argument('--poll_character_limit', type=int, help='character limit for polls (stock Mastodon is limited to 50, so this defaults to 50)', default=50)
parser.add_argument('--poll_run_time', type=int, help='How long the poll will run in hours (defaults to 8)', default=8)
parser.add_argument('--number_of_cues', type=int, help='number of cues for the poll (defaults to 3)', default=3)
parser.add_argument('-p', '--prompt', action='store_true', help='using text prompt to test your story, does not post to Mastodon')
parser.add_argument('-n', '--new', action='store_true', help='start a new story')
parser.add_argument('-e', '--end', action='store_true', help='end the story')
parser.add_argument('-t', '--tag', action='append', type=str, help='hashtag to use in posts, you can add multiple tag flags') # to be implemented
args = parser.parse_args()


print("\n########################\nToot your own adventure!\n########################\n")


story = Story(
    genre=args.genre,
    api_key=args.openai_api_key,
    organization=args.openai_organization,
    poll_character_limit=args.poll_character_limit,
    number_of_cues=args.number_of_cues
)


if args.prompt:
    paragraphs = story.start()
    for i in range(100):
        print(story)
        story.prompt()
    exit()


mastodon = Mastodon(access_token=args.mastodon_access_token, mastodon_server=args.mastodon_server)


if args.new or not mastodon.last_poll:
    print("Starting new story")
    story.start()
    status = story.generate_status(story.get_cues())
    response = mastodon.post_poll(status=status, options=[cue["summary"] for cue in story.get_cues()], expires_in=args.poll_run_time*60*60)
    print(response)
    exit()


if args.end:
    if mastodon.last_status['poll'] == None:
        print("Story has already ended")
        exit()

    print("Ending story")
    
    previous_paragraphs = mastodon.get_paragraphs_from_previous_polls()
    print(f"previous paragraphs\n{previous_paragraphs}\n\n")

    cue = mastodon.get_winning_cue_from_last_poll()
    print(f"previous winning cue: {cue}\n\n")

    story.append_previous_paragraphs(paragraphs=previous_paragraphs)
    print(f"converstaion sent to bot: {story.messages}\n\n")

    story.wrap_up_with_cue(cue)
    print(f"story wrap up: {story.last_paragraph()}\n\n")

    status = story.generate_status()
    print(f"status to post: {status}\n\n")

    previous_poll_id = mastodon.last_poll['id']
    print(f"replying to poll: {previous_poll_id}\n\n")

    response = mastodon.post_status(status=status, previous_poll_id=previous_poll_id)
    print(response)
    exit()


if mastodon.is_last_poll_expired():
    print("Last poll expired, continuing story\n\n\n")

    previous_paragraphs = mastodon.get_paragraphs_from_previous_polls()
    print(f"previous paragraphs\n{previous_paragraphs}\n\n")

    cue = mastodon.get_winning_cue_from_last_poll()
    print(f"previous winning cue: {cue}\n\n")

    story.append_previous_paragraphs(paragraphs=previous_paragraphs)
    print(f"converstaion sent to bot: {story.messages}\n\n")

    story.continue_with_cue(cue)
    print(f"next paragraph: {story.last_paragraph()}\n\n")

    new_cues = story.get_cues()
    print(f"new cues: {new_cues}\n\n")

    status = story.generate_status(new_cues)
    print(f"status to post: {status}\n\n")

    options = [cue["summary"] for cue in new_cues]
    print(f"poll options: {options}\n\n")

    previous_poll_id = mastodon.last_poll['id']
    print(f"replying to poll: {previous_poll_id}\n\n")

    response = mastodon.post_poll(status=status, options=options, expires_in=args.poll_run_time*60*60, previous_poll_id=previous_poll_id)
    print(response)
    exit()

print("Last poll is still running, waiting for it to expire")
