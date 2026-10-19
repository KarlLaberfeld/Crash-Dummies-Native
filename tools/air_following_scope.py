"""Read-only capture selection after the first Air retry; never native input."""
class FollowingAirCaptureScope:
    def __init__(self,following=False,retry=1):
        if type(retry) is not int or retry not in (1,2,3,4):raise ValueError('Unowned reference retry index')
        self.following=bool(following);self.instruction_seen=False;self.ready=not self.following;self.display_offset=0;self.result_seen=False
        self.retry=retry;self.entered=0;self.instruction_pending=False

    def observe(self,pc,display,samples=0):
        if pc==0x268b and display in (2,10):self.instruction_seen=True;self.instruction_pending=True
        if pc==0x03d8 and display==4 and self.instruction_pending:
            self.entered+=1;self.instruction_pending=False
            if self.entered>=self.retry:self.ready=True
        if self.following and self.ready and pc==0x0462 and display in (2,10) and not self.result_seen:
            self.display_offset=samples;self.result_seen=True

    def samples(self,display):
        return display in (2,10) or self.instruction_seen and display in (1,4,5,6)


def instruction_capture_scope(args):
    following=getattr(args,'following',False);retry=getattr(args,'after_retry',1)
    if type(retry) is not int or retry not in (1,2,3):raise ValueError('Unowned instruction generation')
    if retry!=1 and not following:raise ValueError('Later instruction selection requires --following')
    return FollowingAirCaptureScope(following,retry)


def retry_capture_scope(args):
    following=getattr(args,'next_retry',False);retry=getattr(args,'after_retry',1)
    if type(retry) is not int or retry not in (1,2,3):raise ValueError('Unowned entry generation')
    if retry!=1 and not following:raise ValueError('Later entry selection requires --next-retry')
    return FollowingAirCaptureScope(following,retry)


def result_capture_scope(args):
    next_retry=getattr(args,'next_retry',False);after=getattr(args,'after_retry',1)
    if type(after) is not int or after not in (1,2,3) or after!=1 and not next_retry:raise ValueError('Later result selection requires --next-retry')
    return FollowingAirCaptureScope(getattr(args,'following',False) or next_retry,after+1 if next_retry else 1)
