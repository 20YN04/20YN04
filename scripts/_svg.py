"""Shared reveal helpers.

Why SMIL, and why the odd first keyframe.

Some renderers freeze animations inside an <img> at their first frame. Chrome
does it when "Play animations" is off, and it does not report
prefers-reduced-motion when it happens, so a media query cannot catch it. A
reveal that starts hidden then leaves the art invisible forever on those
machines — three empty cards.

Measured behaviour: a frozen renderer paints the animation's value at t=0, NOT
the element's base attribute. So the fallback has to live at t=0.

Every animation here therefore starts ON its finished value, drops to the start
value one ten-thousandth in, holds, then eases back. Frozen renderers paint the
finished art. Live renderers lose the finished value after a fraction of a
frame and play the reveal normally.

Every animation begins at 0s and encodes its stagger in keyTimes, so there is
no pre-begin gap where a delayed element would flash in first.
"""

EASE = ".22 1 .36 1"
LEAD = 0.0001          # how long the finished value is held at t=0
HOLD = "0 0 1 1"       # linear, for the segments that just hold


def _times(delay, fade):
    dur = delay + fade
    split = max(LEAD, (delay / dur) if dur > 0 else LEAD)
    return dur, split


def reveal(delay, fade=0.46, hidden="0", shown="1", attr="opacity"):
    """Fade in after `delay`. Reads as finished when frozen at t=0."""
    dur, split = _times(delay, fade)
    return ('<animate attributeName="%s" values="%s;%s;%s;%s" '
            'keyTimes="0;%.6f;%.6f;1" dur="%.3fs" fill="freeze" '
            'calcMode="spline" keySplines="%s;%s;%s"/>'
            % (attr, shown, hidden, hidden, shown, LEAD, split, dur,
               HOLD, HOLD, EASE))


def slide(delay, fade=0.46, dx=-10.0):
    """Matching translate, settled at t=0 for the same reason."""
    dur, split = _times(delay, fade)
    return ('<animateTransform attributeName="transform" type="translate" '
            'values="0 0;%.1f 0;%.1f 0;0 0" keyTimes="0;%.6f;%.6f;1" '
            'dur="%.3fs" fill="freeze" calcMode="spline" keySplines="%s;%s;%s"/>'
            % (dx, dx, LEAD, split, dur, HOLD, HOLD, EASE))


def wipe(width, dur):
    """Grow a clip rect from 0 to full, starting fully open at t=0."""
    return ('<animate attributeName="width" values="%.2f;0;%.2f" '
            'keyTimes="0;%.6f;1" dur="%.3fs" fill="freeze" calcMode="spline" '
            'keySplines="%s;%s"/>' % (width, width, LEAD, dur, HOLD, EASE))


def playhead(dur):
    """The sweep marker: absent at t=0, so a frozen render never shows it."""
    return ('<animate attributeName="opacity" values="0;1;1;0" '
            'keyTimes="0;%.6f;0.88;1" dur="%.3fs" fill="freeze"/>'
            % (LEAD, dur))
