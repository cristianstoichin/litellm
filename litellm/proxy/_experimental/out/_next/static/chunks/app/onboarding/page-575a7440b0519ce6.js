(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[461],{32922:function(e,s,t){Promise.resolve().then(t.bind(t,12011))},12011:function(e,s,t){"use strict";t.r(s),t.d(s,{default:function(){return Z}});var l=t(57437),n=t(2265),a=t(99376),i=t(20831),r=t(94789),o=t(12514),u=t(49804),c=t(67101),d=t(84264),m=t(49566),h=t(96761),x=t(84566),f=t(19250),p=t(27129),j=t(14474),_=t(13634),g=t(73002);function Z(){let[e]=_.Z.useForm(),s=(0,a.useSearchParams)();!function(e){console.log("COOKIES",document.cookie);let s=document.cookie.split("; ").find(s=>s.startsWith(e+"="));s&&s.split("=")[1]}("token");let t=s.get("invitation_id"),[Z,w]=(0,n.useState)(null),[b,S]=(0,n.useState)(""),[k,N]=(0,n.useState)(""),[v,y]=(0,n.useState)(null),[E,I]=(0,n.useState)(""),[O,C]=(0,n.useState)("");return(0,n.useEffect)(()=>{t&&(0,f.W_)(t).then(e=>{let s=e.login_url;console.log("login_url:",s),I(s);let t=e.token,l=(0,j.o)(t);C(t),console.log("decoded:",l),w(l.key),console.log("decoded user email:",l.user_email),N(l.user_email),y(l.user_id)})},[t]),(0,l.jsx)("div",{className:"mx-auto w-full max-w-md mt-10",children:(0,l.jsxs)(o.Z,{children:[(0,l.jsx)(h.Z,{className:"text-sm mb-5 text-center",children:"\uD83D\uDE85 LiteLLM"}),(0,l.jsx)(h.Z,{className:"text-xl",children:"Sign up"}),(0,l.jsx)(d.Z,{children:"Claim your user account to login to Admin UI."}),(0,l.jsx)(r.Z,{className:"mt-4",title:"SSO",icon:x.GH$,color:"sky",children:(0,l.jsxs)(c.Z,{numItems:2,className:"flex justify-between items-center",children:[(0,l.jsx)(u.Z,{children:"SSO is under the Enterprise Tirer."}),(0,l.jsx)(u.Z,{children:(0,l.jsx)(i.Z,{variant:"primary",className:"mb-2",children:(0,l.jsx)("a",{href:"https://forms.gle/W3U4PZpJGFHWtHyA9",target:"_blank",children:"Get Free Trial"})})})]})}),(0,l.jsxs)(_.Z,{className:"mt-10 mb-5 mx-auto",layout:"vertical",onFinish:e=>{console.log("in handle submit. accessToken:",Z,"token:",O,"formValues:",e),Z&&O&&(e.user_email=k,v&&t&&(0,f.m_)(Z,t,v,e.password).then(e=>{var s;let t="/ui/";t+="?userID="+((null===(s=e.data)||void 0===s?void 0:s.user_id)||e.user_id),(0,p.b)(O),console.log("redirecting to:",t),window.location.href=t}))},children:[(0,l.jsxs)(l.Fragment,{children:[(0,l.jsx)(_.Z.Item,{label:"Email Address",name:"user_email",children:(0,l.jsx)(m.Z,{type:"email",disabled:!0,value:k,defaultValue:k,className:"max-w-md"})}),(0,l.jsx)(_.Z.Item,{label:"Password",name:"password",rules:[{required:!0,message:"password required to sign up"}],help:"Create a password for your account",children:(0,l.jsx)(m.Z,{placeholder:"",type:"password",className:"max-w-md"})})]}),(0,l.jsx)("div",{className:"mt-10",children:(0,l.jsx)(g.ZP,{htmlType:"submit",children:"Sign Up"})})]})]})})}}},function(e){e.O(0,[665,441,899,250,971,117,744],function(){return e(e.s=32922)}),_N_E=e.O()}]);