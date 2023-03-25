import requests
import json
import re
import html

class Mastodon:
    def __init__(self, mastodon_server, access_token):
        self.mastodon_api_url = f"https://{mastodon_server}/api/v1"
        self.access_token = access_token
        self.headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        self.account_id = self.get_account_id()
        self.previous_statuses = self.get_previous_statuses()
        self.last_status = self.previous_statuses[0] if len(self.previous_statuses) > 0 else None
        self.previous_polls = self.get_previous_polls()
        self.last_poll = self.previous_polls[0] if len(self.previous_polls) > 0 else None


    def last_status_is_not_poll(self):
        return self.last_status is not None and self.last_status.get('poll') is None
    

    def last_status_is_poll(self):
        return self.last_status is not None and self.last_status.get('poll') is not None
        

    def get_account_id(self):
        response = requests.get(f"{self.mastodon_api_url}/accounts/verify_credentials", headers=self.headers)
        return json.loads(response.content)["id"]
    

    def get_previous_statuses(self):
        params = {'access_token': self.access_token, 'limit': 50}
        response = requests.get(f"{self.mastodon_api_url}/accounts/{self.account_id}/statuses", params=params)
        return json.loads(response.content)


    def get_previous_polls(self):
        return [status for status in self.previous_statuses if status["poll"]]


    def is_last_poll_expired(self):
        return self.previous_polls[0]["poll"]["expired"] if len(self.previous_polls) > 0 else None

    
    def get_last_poll_winner(self):
        if self.previous_polls:
            results = self.previous_polls[0]["poll"]["options"]
            return max(range(len(results)), key=lambda x: results[x]['votes_count'])


    def get_paragraphs_from_previous_polls(self):
        paragraphs = []
        for poll in self.previous_polls:
            paragraph = self.extract_paragraph_from_poll_content(poll["content"])
            if paragraph:
                paragraphs.insert(0, self.clean_content(paragraph))
            if poll['in_reply_to_id'] is None:
                break
        return paragraphs
            

    def extract_paragraph_from_poll_content(self, content):
        result = re.search(r"(.*?)<p>What should happen next\?</p>", content, re.DOTALL)
        return result.group(1) if result else None


    def extract_cues_from_poll_content(self, content):
        pattern = r'\d+:\s*(.*?)(?:<br\s*/>|<\/p>)'
        return re.findall(pattern, content)


    def get_winning_cue_from_last_poll(self):
        if self.previous_polls:
            winner = self.get_last_poll_winner()
            cues = self.extract_cues_from_poll_content(self.previous_polls[0]["content"])
            return cues[winner]


    def clean_content(self, content):
        return html.unescape(re.sub('<[^<]+?>', '', content)).strip()


    def post_poll(self, status, options, expires_in, previous_poll_id=None):
        poll_data = {
            'options': options,
            'expires_in': expires_in
        }
        status_data = {
            'status': status,
            'poll': poll_data,
            'in_reply_to_id': previous_poll_id
        }
        response = requests.post(f"{self.mastodon_api_url}/statuses", data=json.dumps(status_data), headers=self.headers)
        return json.loads(response.content)


    def post_status(self, status, previous_poll_id=None):
        status_data = {
            'status': status,
            'in_reply_to_id': previous_poll_id
        }
        response = requests.post(f"{self.mastodon_api_url}/statuses", data=json.dumps(status_data), headers=self.headers)
        return json.loads(response.content)