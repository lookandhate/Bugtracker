// document.getElementById("new_member").addEventListener("click",function() { get_Username(project_id);}, false);


function get_Username(project_id) {
  var username = prompt("Enter username ");
  if(username === null) {
    return;
  }
  window.location.href = "/projects/" + project_id + "/manage/add_member/?username=" +  username;
}
