"""Functions for presenting data in human-readable forms."""


def duration(seconds):
    """Return a string of the form "1 hr 2 min 3 sec" representing the
    given number of seconds."""
    if seconds < 1:
        return 'less than 1 sec'
    seconds = int(round(seconds))
    components = []
    for magnitude, label in ((3600, 'hr'), (60, 'min'), (1, 'sec')):
        if seconds >= magnitude:
            components.append('{} {}'.format(seconds // magnitude, label))
            seconds %= magnitude
    return ' '.join(components)


def filesize(num_bytes):
    """Return a string containing an approximate representation of
    *num_bytes* using a small number and decimal SI prefix."""
    for prefix in '-KMGTEPZY':
        if num_bytes < 999.9:
            break
        num_bytes /= 1000.0
    if prefix == '-':
        return '{} B'.format(num_bytes)
    return '{:.3n} {}B'.format(num_bytes, prefix)
