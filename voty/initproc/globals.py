from datetime import date


class NOTIFICATIONS:
    """
    All internal notifications
    """
    class INVITE:
        SEND = "inivited"
        ACCEPTED = "invite_accepted"
        REJECTED = "invite_rejected"

    class INITIATIVE:
        EDITED = "init_edited"
        SUBMITTED = "init_submitted"
        PUBLISHED = "init_published"
        WENT_TO_DISCUSSION = "init_discussion"
        DISCUSSION_CLOSED = "init_discussion_closed"
        WENT_TO_VOTE = 'init_vote'
        COMPLETED = 'init_completed'
        ACCEPTED = 'init_accepted'
        REJECTED = 'init_rejected'
        NEW_ARGUMENT = 'init_new_arg'
        
    class ISSUE_INVITE:
        SEND = "issue_invited"
        ACCEPTED = "issue_invite_accepted"
        REJECTED = "issue_invite_rejected"

    class ISSUE:
        EDITED = "issue_edited"
        DELETED = "issue_deleted"
        SUBMITTED = "issue_submitted"
        EDITED_NEWREVIEW = "issue_edited_newreview"
        PUBLISHED = "issue_published"
        REJECTED = "issue_rejected"
        CLOSED = "issue_closed"
        WENT_TO_DISCUSSION = "issue_discussion"
        FINAL_REVIEW = "issue_final_review"
        WENT_TO_VOTE = 'issue_vote'
        VOTED = 'issue_voted'
        COMPLETED = 'issue_completed'
        NEW_ARGUMENT = 'issue_new_arg'
        VETO = 'veto'

    class SOLUTION:
        EDITED = "solution_edited"
        EDITED_NEWREVIEW = "solution_edited_newreview"
        REJECTED = "solution_rejected"

class STATES:
    """
    The states an initiative can have
    """
    PREPARE = 'p'
    INCOMING = 'i'
    SEEKING_SUPPORT = 's'
    DISCUSSION = 'd'
    FINAL_EDIT = 'e'
    MODERATION = 'm'
    HIDDEN = 'h'
    VOTING = 'v'
    COMPLETED = 'c'
    ACCEPTED = 'a'
    REJECTED = 'r'
    VETO = 'x'


PUBLIC_STATES = [STATES.SEEKING_SUPPORT,
                 STATES.DISCUSSION,
                 STATES.FINAL_EDIT,
                 STATES.VOTING,
                 STATES.COMPLETED,
                 STATES.ACCEPTED,
                 STATES.REJECTED,
                 STATES.VETO]

TEAM_ONLY_STATES = [STATES.INCOMING,
                    STATES.MODERATION,
                    STATES.HIDDEN]

class VOTY_TYPES:
    Einzelinitiative = 'initiative'
    PolicyChange = 'ao-aenderung'
    BallotVote = 'urabstimmung'
    PlenumVote = 'plenumsentscheidung'
    PlenumOptions = 'plenumsabwaegung'
    Contribution = 'beitrag'

class VOTED:
    """
    The possibilities for casting a vote
    """
    NO = 0
    YES = 1
    ABSTAIN = 2


COMPARING_FIELDS = [
    'title', 'subtitle',  "summary", "problem", "forderung", "kosten",
    "fin_vorschlag", "arbeitsweise", "init_argument",
    "einordnung", "ebene", "bereich",
    "motivation", "description", "budget"
]

ADMINISTRATIVE_LEVELS = [
    'Bund',
    'Baden-Württemberg',
    'Bayern',
    'Berlin',
    'Brandenburg',
    'Bremen',
    'Hamburg',
    'Hessen',
    'Mecklenburg-Vorpommern',
    'Niedersachsen',
    'Nordrhein-Westfalen',
    'Rheinland-Pfalz',
    'Saarland',
    'Sachsen',
    'Sachsen-Anhalt',
    'Schleswig-Holstein',
    'Thüringen',
    'Leinfelden-Echterdingen',
    'Stuttgart',
    'Tübingen',
]

SUBJECT_CATEGORIES = [
    'Globale Politik & internationale Zusammenarbeit',
    'Bildung, Forschung & Kultur',
    'Innenpolitik',
    'Netz- & Medienpolitik',
    'Geschlechtergerechtigkeit',
    'Vielfalt & Integration',
    'Demokratie & Transparenz',
    'Gesundheit, Ernährung & Verbraucher*innenschutz',
    'Umwelt, Mobilität, Infrastruktur & Strukturentwicklung',
    'Soziale Gerechtigkeit, Wirtschaft, Arbeit & Finanzen',
    'Anderes'
]

ABSTENTION_START = date(2017, 12, 1) # Everything published after this has abstentions
SPEED_PHASE_END = date(2017, 8, 21) # Everything published before this has speed phase
INITIATORS_COUNT = 3

MINIMUM_MODERATOR_VOTES = 5
MINIMUM_FEMALE_MODERATOR_VOTES = 3
MINIMUM_DIVERSE_MODERATOR_VOTES = 2

MINIMUM_REVIEW_TEAM_SIZE = 5

CONTRIBUTION_QUORUM = 6

BOARD_GROUP = "Bundesvorstand"