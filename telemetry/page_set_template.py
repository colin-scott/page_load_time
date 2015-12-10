"""Template page set file. Non functional python.

Must fill in {0} with the name of the page set and {1} with the url
"""
from telemetry.page import page
from telemetry.page import page_set


class {0}PageSet(page_set.PageSet):
  def __init__(self):
    super({0}PageSet, self).__init__(
        user_agent_type='mobile',
        # user_agent_type='tablet',
        # user_agent_type='desktop',
        archive_data_file='data/{0}_page_set.json',
        bucket=page_set.PUBLIC_BUCKET)
    self.AddUserStory(page.Page(
        name='{0}',
        url='{1}',
        page_set=self))
