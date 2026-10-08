const theme=document.getElementById("theme");
if(localStorage.getItem("theme")==="dark"){document.body.classList.add("dark");if(theme)theme.textContent="☀";}
if(theme) theme.addEventListener("click",()=>{document.body.classList.toggle("dark");const d=document.body.classList.contains("dark");localStorage.setItem("theme",d?"dark":"light");theme.textContent=d?"☀":"☾";});
setTimeout(()=>document.querySelectorAll(".alert").forEach(x=>x.remove()),4500);
