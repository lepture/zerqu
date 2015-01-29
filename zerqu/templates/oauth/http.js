function $(id) {
  return document.getElementById(id);
}

function login(resp) {
  if (resp.status !== 'ok') {
    return;
  }
  var data = resp.data;
  $('user-avatar').setAttribute('src', data.avatar_url);
  $('user-name').innerHTML = data.username;
  if (data.description) {
    $('user-description').innerHTML = data.description;
  }
  $('cancel-button').className = '';
  showConfirm();
}

function showConfirm() {
  $('user-info').className = 'clearfix';
  $('login-form').className = 'hide';
  $('confirm-form').className = '';
}

$('change-account').addEventListener('click', function(e) {
  e.preventDefault();
  $('user-info').className = 'clearfix hide';
  $('login-form').className = '';
  $('confirm-form').className = 'hide';
}, false);

$('cancel-button').addEventListener('click', function(e) {
  e.preventDefault();
  showConfirm();
}, false);

$('login-button').addEventListener('click', function(e) {
  e.preventDefault();
  var req = new XMLHttpRequest();
  req.open('POST', '/session');
  req.onreadystatechange = function(){
    if (4 === req.readyState) {
      var type = req.status / 100 | 0;
      if (2 === type) {
        login(JSON.parse(req.response));
      } else {
        var err = new Error(req.statusText + ': ' + req.response);
        err.status = req.status;
        throw(err);
      }
    }
  };
  req.setRequestHeader('Content-Type', 'application/json');
  req.send(JSON.stringify({
    username: $('username').value,
    password: $('password').value
  }));
});
