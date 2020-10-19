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
              <i class="material-icons">email</i>${item.actor} hat Dich zu "${item.target}" eingeladen
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
          
        // ISSUE_INVITES
        case "issue_invited":
          message = `<a href="/issue/${item.target_object_id}">
              <i class="material-icons">email</i>${item.actor} hat Dich zu "${item.target}" eingeladen
          </a>`
          break;
        case "issue_invite_accepted":
          message = `<a href="/issue/${item.target_object_id}">
              <i class="material-icons">check</i>${item.actor} hat die Einladung zu "${item.target}" angenommen
          </a>`
          break;

        case "issue_invite_rejected":
          message = `<a href="/issue/${item.target_object_id}">
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

        case "init_discussion":
            message = `<a href="/initiative/${item.actor_object_id}">
                <i class="material-icons">forum</i>${item.actor} kann jetzt diskutiert werden.
            </a>`
          break;

        case "init_discussion_closed":
            message = `<a href="/initiative/${item.actor_object_id}">
                <i class="material-icons">create</i>${item.actor} kann jetzt final editiert werden.
            </a>`
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
                <i class="material-icons">comment</i>${item.actor} hat ein neues Argument zu "${item.target}" veröffentlicht.
            </a>`
          break;

        // ISSUES

        case "issue_edited":
          message = `<a href="/issue/${item.target_object_id}">
              <i class="material-icons">mode_edit</i>${item.actor} hat "${item.target}" verändert
          </a>`
          break;

        case "issue_deleted":
          message = `<a href="/issue/${item.target_object_id}">
              <i class="material-icons">mode_edit</i>${item.actor} hat "${item.target}" gelöscht
          </a>`
          break;

        case "issue_submitted":
            message = `<a href="/issue/${item.target_object_id}">
                <i class="material-icons">publish</i>${item.actor} hat "${item.target}" eingereicht
            </a>`
          break;

        case "issue_edited_newreview":
          message = `<a href="/issue/${item.target_object_id}">
              <i class="material-icons">mode_edit</i>${item.actor} hat "${item.target}" verändert. Bitte prüfe erneut.
          </a>`
          break;

        case "issue_published":
          if (item.target){
            message = `<a href="/issue/${item.target_object_id}">
                <i class="material-icons">public</i>${item.actor} hat "${item.target}" veröffentlicht
            </a>`
          } else {
            message = `<a href="/issue/${item.actor_object_id}">
                <i class="material-icons">public</i>${item.actor} wurde veröffentlicht
            </a>`
          }
          break;

        case "issue_rejected":
          if (item.target){
            message = `<a href="/issue/${item.target_object_id}">
                <i class="material-icons">public</i>${item.actor} hat "${item.target}" abgelehnt
            </a>`
          } else {
            message = `<a href="/issue/${item.actor_object_id}">
                <i class="material-icons">public</i>${item.actor} wurde nach Prüfung abgelehnt
            </a>`
          }
          break;

        case "issue_closed":
            message = `<a href="/issue/${item.actor_object_id}">
                <i class="material-icons">block</i>${item.actor} wurde mangels Unterstützung geschlossen.
            </a>`
          break;

        case "issue_discussion":
          if (item.target){
            message = `<a href="/issue/${item.target_object_id}">
                <i class="material-icons">forum</i>${item.target} kann jetzt diskutiert werden.
            </a>`
          } else {
            message = `<a href="/issue/${item.actor_object_id}">
                <i class="material-icons">forum</i>${item.actor} kann jetzt diskutiert werden.
            </a>`
          }
          break;

        case "issue_final_review":
            message = `<a href="/issue/${item.actor_object_id}">
                <i class="material-icons">check</i>Alle Lösungsvorschläge zu ${item.actor} prüfen!
            </a>`
          break;
          
        case "issue_vote":
          if (item.target){
            message = `<a href="/issue/${item.target_object_id}">
                <i class="material-icons">thumbs_up_down</i>${item.actor} hat "${item.target}" zur Abstimmung frei gegeben
            </a>`
          } else {
            message = `<a href="/issue/${item.actor_object_id}">
                <i class="material-icons">thumbs_up_down</i>${item.actor} steht jetzt zur Abstimmung
            </a>`
          }
          break;

        case "issue_voted":
            message = `<a href="/issue/${item.actor_object_id}">
                <i class="material-icons">check</i>${item.actor} wurde abgestimmt.
            </a>`
          break;

        case "veto":
          if (item.target){
            message = `<a href="/issue/${item.target_object_id}">
                <i class="material-icons">block</i>${item.actor} hat zu "${item.target}" ein Veto abgegeben
            </a>`
          } else {
            message = `<a href="/issue/${item.actor_object_id}">
                <i class="material-icons">block</i>${item.actor} wurde durch ein Veto abgelehnt
            </a>`
          }
          break;

        // SOLUTIONS
        
        case "solution_edited":
          message = `<a href="/solution/${item.target_object_id}">
              <i class="material-icons">mode_edit</i>${item.actor} hat "${item.target}" verändert
          </a>`
          break;
          
        case "solution_edited_newreview":
          message = `<a href="/solution/${item.target_object_id}">
              <i class="material-icons">mode_edit</i>${item.actor} hat "${item.target}" verändert. Bitte prüfe erneut.
          </a>`
          break;

        case "solution_rejected":
          if (item.target){
            message = `<a href="/solution/${item.target_object_id}">
                <i class="material-icons">public</i>${item.actor} hat Lösungsvorschlag "${item.target}" abgelehnt
            </a>`
          } else {
            message = `<a href="/solution/${item.actor_object_id}">
                <i class="material-icons">public</i>${item.actor} wurde nach Prüfung abgelehnt
            </a>`
          }
          break;

        case "solution_new_arg":
            message = `<a href="/solution/${item.target_object_id}">
                <i class="material-icons">comment</i>${item.actor} hat ein neues Argument zu "${item.target}" veröffentlicht.
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

function setup_char_counter(prefix){
  // automatically show counter for all text-fields where applicable
  $((prefix || '') + "[maxlength]").keyup(function(evt){
    var t = $(evt.currentTarget);
    $('[for=' + t.attr('id') + ']'
      ).attr("data-text-after", "(noch " + (parseInt(t.attr('maxlength')) - t.val().replace(/\n/g,"\n\n").length) + " Zeichen)");
  }).keyup();

}


$(function() {
  setup_char_counter();
});