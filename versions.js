arr = window.location.href.split('/');
page = arr[arr.length - 1];
document.write('\
<dl>\
    <dt>Versions</dt> \
    <dd><a href="../master/' + page + '">master</a></dd>\
    <dd><a href="../2.1/' + page + '">2.1</a></dd>\
    <dd><a href="../2.0/' + page + '">2.0</a></dd>\
    <dd><a href="../1.1/' + page + '">1.1</a></dd>\
    <dd><a href="../1.0/' + page + '">1.0</a></dd>\
</dl>\
');