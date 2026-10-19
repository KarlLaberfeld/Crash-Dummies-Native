"""Read-only capture selection after the first Air retry; never native input."""
class FollowingAirCaptureScope:
    def __init__(self,following=False):
        self.following=bool(following);self.instruction_seen=False;self.ready=not self.following;self.display_offset=0;self.result_seen=False

    def observe(self,pc,display,samples=0):
        if pc==0x268b and display in (2,10):self.instruction_seen=True
        if pc==0x03d8 and display==4 and self.instruction_seen:self.ready=True
        if self.following and self.ready and pc==0x0462 and display in (2,10) and not self.result_seen:
            self.display_offset=samples;self.result_seen=True

    def samples(self,display):
        return display in (2,10) or self.instruction_seen and display in (1,4,5,6)
