(function(){
  const OLD='头脑风暴', NEW='思维导图/流程图';
  const attrs=['title','aria-label','placeholder','value'];
  function fixNode(root){
    if(!root)return;
    const fixEl=(el)=>{
      if(!el||el.nodeType!==1)return;
      const tag=el.tagName;
      if(tag==='SCRIPT'||tag==='STYLE'||tag==='TEMPLATE')return;
      for(const a of attrs){
        if(el.hasAttribute&&el.hasAttribute(a)){
          const v=el.getAttribute(a);
          if(v&&v.includes(OLD))el.setAttribute(a,v.split(OLD).join(NEW));
        }
      }
      if((tag==='INPUT'||tag==='TEXTAREA')&&typeof el.value==='string'&&el.value.includes(OLD))el.value=el.value.split(OLD).join(NEW);
    };
    if(root.nodeType===3){
      const p=root.parentElement,tag=p&&p.tagName;
      if(tag!=='SCRIPT'&&tag!=='STYLE'&&tag!=='TEMPLATE'&&root.nodeValue&&root.nodeValue.includes(OLD))root.nodeValue=root.nodeValue.split(OLD).join(NEW);
      return;
    }
    if(root.nodeType!==1&&root.nodeType!==9&&root.nodeType!==11)return;
    if(root.nodeType===1)fixEl(root);
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT);
    let n;
    while((n=walker.nextNode())){
      if(n.nodeType===1)fixEl(n);
      else if(n.nodeType===3){
        const p=n.parentElement,tag=p&&p.tagName;
        if(tag!=='SCRIPT'&&tag!=='STYLE'&&tag!=='TEMPLATE'&&n.nodeValue&&n.nodeValue.includes(OLD))n.nodeValue=n.nodeValue.split(OLD).join(NEW);
      }
    }
  }
  fixNode(document.documentElement);
  new MutationObserver(ms=>ms.forEach(m=>{
    if(m.type==='characterData')fixNode(m.target);
    else m.addedNodes.forEach(fixNode);
  })).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
})();
