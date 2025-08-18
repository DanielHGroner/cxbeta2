function refreshAll(e) {
    console.log('in refreshAll', e);

    // is there a current statement?
    const currentHilited = currentHighlightedSpan;
    console.log('current hilited:', currentHilited);

    if (!currentHilited) {
        console.log('current hilited is null, returning from refreshAll');
        return;
    }

    // get the currently highlighted item's id
    const id = currentHilited ? currentHilited.id || currentHilited.getAttribute('id') : null;
    console.log('current hilited id:', id);

    // check if the currently hilited span is a statement
    const isStatement = !!(currentHilited && currentHilited.classList.contains('cx-statement'));

    if (!isStatement) {
       console.log('current hilited is not a statement, returning from refreshAll');
       return;
    }

    console.log('current hilited is a statement');

    // handle if the current statement became hidden, but selecting the special -deselect <span>
    isHidden = currentHilited.classList.contains('cx-hidden') || currentHilited.getClientRects().length === 0;
    if (isHidden) {
       console.log('current hilited is now a hidden statement');
       // TODO - simulate click on -deselect span
       deselect_span = document.getElementById('-deselect');
       console.log('got deselect span from id:', deselect_span);
       console.log('dispatching mouse click to deselect span');
       deselect_span.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
       currentHighlightedSpan = deselect_span;
       return;
    }

    // simulate a mouse click on the originally (and still) selected statement, to trigger refreshed arrows (and hopefully help)
    currentHilited.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));

    console.log('returning from refreshAll()')
}