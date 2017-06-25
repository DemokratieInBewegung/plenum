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
        WENT_TO_DEBATE = "init_debatable"
        WENT_TO_VOTE = 'init_vote'


class STATES:
    """
    The states and initiative can have
    """
    PREPARE = 'p'
    INCOMING = 'i'
    SEEKING_SUPPORT = 's'
    DISCUSSION = 'd'
    FINAL_EDIT = 'e'
    MODERATION = 'm'
    HIDDEN = 'h'
    VOTING = 'v'
    ACCEPTED = 'a'
    REJECTED = 'r'


PUBLIC_STATES = [STATES.SEEKING_SUPPORT,
                 STATES.DISCUSSION,
                 STATES.FINAL_EDIT,
                 STATES.VOTING,
                 STATES.ACCEPTED,
                 STATES.REJECTED]

STAFF_ONLY_STATES = [STATES.INCOMING,
                     STATES.MODERATION,
                     STATES.HIDDEN]




SPEED_PHASE_END = date(2017, 8, 21) # Everything published before this has speed phase
INITIATORS_COUNT = 3

MINIMUM_MODERATOR_VOTES = 3
