function update_notifications(data) {
  // for the django notifications top right.
  // https://github.com/django-notifications/django-notifications#how-to-use
  var menu = document.getElementById(notify_menu_id);
  if (menu) {
    var content = [];
    menu.innerHTML = data.unread_list.map(function (item) {
      var message = "";
      switch (item.verb) {
        // INVITES
        case "inivited":
          message = `<a href="/initiative/${item.target_object_id}">
              <i class="material-icons">email</i>${item.actor} hat dich zu "${item.target}" eingeladen
          </a>`
          break;
        case "invite_accepted":
          message = `<a href="/initiative/${item.target_object_id}">
              <i class="material-icons">check</i>${item.actor} hat die Einladung zu "${item.target}" angenommen
          </a>`
          break;

        case "invite_rejected":
          message = `<a href="/initiative/${item.target_object_id}">
              <i class="material-icons">block</i>${item.actor} hat die Einladung zu "${item.target}" abgelehnt
          </a>`
          break;

        // INITIATIVES

        case "init_edited":
          message = `<a href="/initiative/${item.target_object_id}">
              <i class="material-icons">mode_edit</i>${item.actor} hat "${item.target}" verändert
          </a>`
          break;

        case "init_submitted":
            message = `<a href="/initiative/${item.target_object_id}">
                <i class="material-icons">publish</i>${item.actor} hat "${item.target}" eingereicht
            </a>`
          break;

        case "init_published":
          if (item.target){
            message = `<a href="/initiative/${item.target_object_id}">
                <i class="material-icons">public</i>${item.actor} hat "${item.target}" veröffentlicht
            </a>`
          } else {
            message = `<a href="/initiative/${item.actor_object_id}">
                <i class="material-icons">public</i>${item.actor} wurde veröffentlicht
            </a>`
          }
          break;


        case "init_vote":
          if (item.target){
            message = `<a href="/initiative/${item.target_object_id}">
                <i class="material-icons">thumbs_up_down</i>${item.actor} hat "${item.target}" zur Abstimmung frei gegeben
            </a>`
          } else {
            message = `<a href="/initiative/${item.actor_object_id}">
                <i class="material-icons">thumbs_up_down</i>${item.actor} steht jetzt zur Abstimmung
            </a>`
          }
          break;

        case "init_new_arg":
            message = `<a href="/initiative/${item.target_object_id}">
                <i class="material-icons">comment</i>${item.actor} hat ein neues Argument zu "${item.target}"" veröffentlicht.
            </a>`
          break;


        default:
          if (typeof item.actor !== 'undefined'){
            message = item.actor;
          }
          if (typeof item.verb !== 'undefined'){
            message = message + " " + item.verb;
          }
          if (typeof item.target !== 'undefined'){
            message = message + " " + item.target;
          }
          if (typeof item.timestamp !== 'undefined'){
            message = message + " " + item.timestamp;
          }
      }
      return '<li>' + message + '</li>';
    }).join('')
  } 
}