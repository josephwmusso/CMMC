import svgPaths from "./svg-grkg5cmmfd";
import imgSlide01Light1 from "figma:asset/3b36e701e0a6181dd6dfa0e5b6fa7eede739df98.png";

function Symbol() {
  return (
    <div className="h-[35px] relative shrink-0 w-[29px]" data-name="symbol">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 29 35">
        <g id="symbol">
          <path d={svgPaths.p3a48e00} fill="var(--fill-0, #3EA9F7)" id="Union" />
        </g>
      </svg>
    </div>
  );
}

function Logo1() {
  return (
    <div className="content-stretch flex gap-[10px] h-[40px] items-start relative shrink-0 w-[29px]" data-name="logo">
      <Symbol />
    </div>
  );
}

function Frame4() {
  return (
    <div className="content-stretch flex flex-col h-[40px] items-start justify-center leading-[0] relative shrink-0 w-[106.25px]">
      <div className="flex flex-[1_0_0] flex-col font-['Bakbak_One:Regular',sans-serif] justify-center min-h-px min-w-px not-italic relative text-[#23262f] text-[20px] tracking-[-0.4px] w-full">
        <p className="leading-[0px]">blocktickets</p>
      </div>
      <div className="flex flex-col font-['Roboto:Medium',sans-serif] font-medium h-[18.75px] justify-center relative shrink-0 text-[#777e90] text-[10px] uppercase w-full" style={{ fontVariationSettings: "'wdth' 100" }}>
        <p className="leading-[0px]">Creator panel</p>
      </div>
    </div>
  );
}

function Logo() {
  return (
    <div className="content-stretch flex gap-[5px] items-start relative shrink-0 w-[282px]" data-name="logo">
      <div aria-hidden="true" className="absolute border-[#e6e8ec] border-r border-solid inset-0 pointer-events-none" />
      <Logo1 />
      <Frame4 />
    </div>
  );
}

function Button() {
  return (
    <div className="bg-[#3ea9f7] content-stretch flex gap-[8px] h-[40px] items-center justify-center px-[16px] py-[8px] relative rounded-[8px] shrink-0" data-name="Button">
      <div className="relative shrink-0 size-[24px]" data-name="Icons/icons/Plus 2/Line">
        <div className="absolute inset-1/4" data-name="Union">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 12 12">
            <path d={svgPaths.p1d60f200} fill="var(--fill-0, white)" id="Union" />
          </svg>
        </div>
      </div>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[14px] text-white whitespace-nowrap">Create an event</p>
    </div>
  );
}

function LeftContent() {
  return (
    <div className="content-stretch flex gap-[32px] items-center relative shrink-0" data-name="Left content">
      <Logo />
      <Button />
      <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[16px] relative shrink-0 text-[#777e90] text-[14px] text-center whitespace-nowrap" style={{ fontVariationSettings: "'opsz' 14" }}>
        Events
      </p>
      <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[16px] relative shrink-0 text-[#777e90] text-[14px] text-center whitespace-nowrap" style={{ fontVariationSettings: "'opsz' 14" }}>
        Reports
      </p>
    </div>
  );
}

function Button1() {
  return (
    <div className="bg-[#f4f5f6] content-stretch flex gap-[8px] h-[40px] items-center justify-center px-[16px] py-[8px] relative rounded-[8px] shrink-0" data-name="Button">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#23262f] text-[14px] whitespace-nowrap">Organization name</p>
      <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/icons/Arrow Down Simple/Line">
        <div className="absolute flex inset-[39.58%_31.25%_37.5%_31.25%] items-center justify-center">
          <div className="-rotate-90 -scale-y-100 flex-none h-[9px] w-[5.5px]">
            <div className="relative size-full" data-name="Shape">
              <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 5.5 9">
                <path clipRule="evenodd" d={svgPaths.p2835b900} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Shape" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Actions() {
  return (
    <div className="content-stretch flex items-start justify-end relative shrink-0" data-name="Actions">
      <Button1 />
    </div>
  );
}

function NavContent() {
  return (
    <div className="content-stretch flex items-center justify-between px-[32px] py-[20px] relative shrink-0 w-[1440px]" data-name="Nav content">
      <LeftContent />
      <Actions />
    </div>
  );
}

function Dropdown() {
  return <div className="bg-white h-[0.01px] shrink-0 w-[1440px]" data-name="dropdown" />;
}

function Frame10() {
  return (
    <div className="content-stretch flex items-center relative shrink-0 w-full">
      <div className="flex flex-[1_0_0] flex-col font-['Poppins:SemiBold',sans-serif] justify-center leading-[0] min-h-px min-w-px not-italic relative text-[#141416] text-[16px]">
        <p className="leading-[24px]">Nic Fanciulli</p>
      </div>
    </div>
  );
}

function Frame11() {
  return (
    <div className="content-stretch flex flex-[1_0_0] items-center min-h-px min-w-px relative">
      <div className="flex flex-[1_0_0] flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] min-h-px min-w-px not-italic relative text-[#141416] text-[14px]">
        <p className="leading-[1.7]">Thu • Mar 13 • 9:00 PM EST</p>
      </div>
    </div>
  );
}

function Frame12() {
  return (
    <div className="content-stretch flex items-start relative shrink-0 w-full">
      <Frame11 />
    </div>
  );
}

function Frame3() {
  return (
    <div className="content-stretch flex flex-col items-start justify-center relative shrink-0 w-full">
      <Frame10 />
      <Frame12 />
    </div>
  );
}

function Frame2() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col items-center justify-center min-h-px min-w-px relative">
      <Frame3 />
    </div>
  );
}

function Frame9() {
  return (
    <div className="content-stretch flex items-center relative shrink-0 w-[421.333px]">
      <Frame2 />
    </div>
  );
}

function Frame49() {
  return (
    <div className="content-stretch flex flex-[1_0_0] items-center min-h-px min-w-px relative">
      <Frame9 />
    </div>
  );
}

function Frame47() {
  return <div className="flex-[1_0_0] h-[64px] min-h-px min-w-px" />;
}

function Frame48() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col items-end justify-center min-h-px min-w-px relative">
      <div className="bg-[rgba(151,87,215,0.12)] content-stretch flex gap-[8px] items-center justify-center px-[16px] py-[4px] relative rounded-[12px] shrink-0" data-name="Tags">
        <div aria-hidden="true" className="absolute border-0 border-[#ef466f] border-solid inset-0 pointer-events-none rounded-[12px]" />
        <div className="flex flex-col font-['Poppins:Medium',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#9757d7] text-[14px] text-right whitespace-nowrap">
          <p className="leading-[24px]">Scheduled</p>
        </div>
        <div className="relative shrink-0 size-[12px]" data-name="Union">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 12 12">
            <path clipRule="evenodd" d={svgPaths.p25d9ae00} fill="var(--fill-0, #9757D7)" fillRule="evenodd" id="Union" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function NavDesktopLightLoggedDropdown() {
  return (
    <div className="bg-white h-[64px] relative shrink-0 w-full" data-name="Nav/Desktop/Light/Logged/Dropdown">
      <div aria-hidden="true" className="absolute border-[#e6e8ec] border-solid border-t inset-0 pointer-events-none" />
      <div className="flex flex-row items-center size-full">
        <div className="content-stretch flex gap-[16px] items-center px-[32px] relative size-full">
          <Frame49 />
          <Frame47 />
          <Frame48 />
        </div>
      </div>
    </div>
  );
}

function Divider() {
  return <div className="bg-[#e6e8ec] h-px shrink-0 w-full" data-name="divider" />;
}

function Left() {
  return (
    <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Left">
      <div className="overflow-clip relative shrink-0 size-[24px]" data-name="UI icon/home/light">
        <div className="absolute inset-[8.48%_8.33%_8.33%_8.33%]" data-name="Union">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 19.9639">
            <path clipRule="evenodd" d={svgPaths.p743b400} fill="var(--fill-0, #6F767E)" fillRule="evenodd" id="Union" />
          </svg>
        </div>
      </div>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Dashboard</p>
    </div>
  );
}

function AddIcon() {
  return (
    <div className="relative shrink-0 size-[8px]" data-name="add icon">
      <div className="absolute inset-[-12.5%]">
        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10 10">
          <g id="add icon">
            <path d="M5 1V9" id="Vector 3" stroke="var(--stroke-0, #6F767E)" strokeLinecap="round" strokeWidth="2" />
            <path d="M1 5L9 5" id="Vector 4" stroke="var(--stroke-0, #6F767E)" strokeLinecap="round" strokeWidth="2" />
          </g>
        </svg>
      </div>
    </div>
  );
}

function Icon() {
  return (
    <div className="absolute left-0 rounded-[24px] top-0" data-name="icon">
      <div className="content-stretch flex items-center justify-center overflow-clip p-[8px] relative rounded-[inherit]">
        <AddIcon />
      </div>
      <div aria-hidden="true" className="absolute border-2 border-[#efefef] border-solid inset-0 pointer-events-none rounded-[24px]" />
    </div>
  );
}

function Left1() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[12px] items-center min-h-px min-w-px relative" data-name="Left">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Event Details</p>
    </div>
  );
}

function Left2() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[12px] items-center min-h-px min-w-px relative" data-name="Left">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Event Settings</p>
    </div>
  );
}

function Left3() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[12px] items-center min-h-px min-w-px relative" data-name="Left">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Seat Map</p>
    </div>
  );
}

function Left4() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[12px] items-center min-h-px min-w-px relative" data-name="Left">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Offers</p>
    </div>
  );
}

function Left5() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[12px] items-center min-h-px min-w-px relative" data-name="Left">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Add-ons</p>
    </div>
  );
}

function Frame13() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0 w-full">
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex gap-[12px] items-center p-[12px] relative w-full">
            <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/UI icon/document/light">
              <div className="absolute bottom-1/2 left-[29.17%] right-[29.17%] top-[41.67%]" data-name="Vector 492 (Stroke)">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10 2">
                  <path clipRule="evenodd" d={svgPaths.pd802880} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Vector 492 (Stroke)" />
                </svg>
              </div>
              <div className="absolute inset-[58.33%_45.83%_33.33%_29.17%]" data-name="Vector 493 (Stroke)">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 6 2">
                  <path clipRule="evenodd" d={svgPaths.p7ff5a00} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Vector 493 (Stroke)" />
                </svg>
              </div>
              <div className="absolute inset-[8.33%_12.5%]" data-name="Union">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 18 20">
                  <path clipRule="evenodd" d={svgPaths.p3bf69c80} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Union" />
                </svg>
              </div>
            </div>
            <Left1 />
          </div>
        </div>
      </div>
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex gap-[12px] items-center p-[12px] relative w-full">
            <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/UI icon/settings/light">
              <div className="absolute inset-[33.33%]" data-name="Oval (Stroke)">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 8 8">
                  <path clipRule="evenodd" d={svgPaths.p20484100} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Oval (Stroke)" />
                </svg>
              </div>
              <div className="absolute inset-[4.17%_7.9%]" data-name="Union (Stroke)">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.2095 22">
                  <path clipRule="evenodd" d={svgPaths.p54642b0} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Union (Stroke)" />
                </svg>
              </div>
            </div>
            <Left2 />
          </div>
        </div>
      </div>
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex gap-[12px] items-center p-[12px] relative w-full">
            <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/UI icon/refund/seat">
              <div className="absolute h-[19px] left-[4px] top-[2px] w-[17px]" data-name="Vector">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 17 19">
                  <path d={svgPaths.p18c0bc70} id="Vector" stroke="var(--stroke-0, #777E91)" strokeWidth="2" />
                </svg>
              </div>
            </div>
            <Left3 />
            <div className="overflow-clip relative shrink-0 size-[16.056px]" data-name="Icons/UI icon/open/light">
              <div className="absolute inset-[12.5%_12.5%_45.83%_45.83%]" data-name="Union">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 6.68981 6.68981">
                  <path d={svgPaths.pe86fe00} fill="var(--fill-0, #777E91)" id="Union" />
                </svg>
              </div>
              <div className="absolute inset-[12.5%]" data-name="Vector 598 (Stroke)">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 12.0417 12.0417">
                  <path clipRule="evenodd" d={svgPaths.p56096c0} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Vector 598 (Stroke)" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex gap-[12px] items-center p-[12px] relative w-full">
            <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/icons/Badge Discount/Line">
              <div className="absolute inset-[8.19%]" data-name="Shape">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.0695 20.0695">
                  <path clipRule="evenodd" d={svgPaths.p17c8d200} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Shape" />
                </svg>
              </div>
              <div className="absolute inset-[37.5%]" data-name="Shape">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 6 6">
                  <g id="Shape">
                    <path d={svgPaths.p19e8400} fill="var(--fill-0, #777E91)" />
                    <path d={svgPaths.p3c91bc00} fill="var(--fill-0, #777E91)" />
                    <path d={svgPaths.p3200cb00} fill="var(--fill-0, #777E91)" />
                  </g>
                </svg>
              </div>
            </div>
            <Left4 />
          </div>
        </div>
      </div>
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex gap-[12px] items-center p-[12px] relative w-full">
            <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/UI icon/puzzle/light">
              <div className="absolute inset-[8.33%_12.5%_12.5%_8.33%]" data-name="Subtract (Stroke)">
                <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 19 19">
                  <path clipRule="evenodd" d={svgPaths.p28452400} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Subtract (Stroke)" />
                </svg>
              </div>
            </div>
            <Left5 />
          </div>
        </div>
      </div>
    </div>
  );
}

function EventDetails() {
  return (
    <div className="content-stretch flex flex-col items-start relative rounded-[12px] shrink-0 w-full" data-name="event details">
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex items-center justify-between p-[12px] relative w-full">
            <Left />
            <div className="content-stretch flex gap-[12px] items-start opacity-0 relative shrink-0" data-name="Icon (right)/couple">
              <div className="bg-[#ffbc99] overflow-clip relative rounded-[6px] shrink-0 size-[24px]" data-name="Number">
                <p className="absolute font-['Inter:Semi_Bold',sans-serif] font-semibold inset-0 leading-[24px] not-italic text-[#1a1d1f] text-[15px] text-center tracking-[-0.15px]">8</p>
              </div>
              <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icon/add">
                <Icon />
              </div>
              <div className="relative shrink-0 size-[24px]" data-name="Cheveron">
                <div className="absolute bottom-[37.5%] left-1/4 right-1/4 top-[37.5%]">
                  <div className="absolute inset-[-16.67%_-8.33%]">
                    <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 8">
                      <path d="M1 1L7 7L13 1" id="Vector 1" stroke="var(--stroke-0, #6F767E)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Frame13 />
    </div>
  );
}

function Divider1() {
  return <div className="bg-[#e6e8ec] h-px shrink-0 w-full" data-name="divider" />;
}

function Left6() {
  return (
    <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Left">
      <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/UI icon/person/light">
        <div className="absolute bottom-1/2 left-[29.17%] right-[29.17%] top-[8.33%]" data-name="Ellipse 132 (Stroke)">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10 10">
            <path clipRule="evenodd" d={svgPaths.p397b8580} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Ellipse 132 (Stroke)" />
          </svg>
        </div>
        <div className="absolute inset-[58.33%_12.5%_8.33%_12.5%]" data-name="Vector 631 (Stroke)">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 18 8">
            <path clipRule="evenodd" d={svgPaths.p1e458f10} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Vector 631 (Stroke)" />
          </svg>
        </div>
      </div>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Manage attendees</p>
    </div>
  );
}

function IconRight() {
  return (
    <div className="content-stretch flex gap-[12px] items-start opacity-0 relative shrink-0" data-name="Icon (right)">
      <div className="relative shrink-0 size-[24px]" data-name="Cheveron">
        <div className="absolute bottom-[37.5%] left-1/4 right-1/4 top-[37.5%]">
          <div className="absolute inset-[-16.67%_-8.33%]">
            <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 8">
              <path d="M1 1L7 7L13 1" id="Vector 1" stroke="var(--stroke-0, #6F767E)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function SubNavItem() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex items-start justify-between p-[12px] relative w-full">
        <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Check-in</p>
        <IconRight />
      </div>
    </div>
  );
}

function SubNavItem1() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex gap-[104px] items-start p-[12px] relative w-full">
        <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Ticket Transfers</p>
      </div>
    </div>
  );
}

function IconRight1() {
  return (
    <div className="content-stretch flex gap-[12px] items-start opacity-0 relative shrink-0" data-name="Icon (right)">
      <div className="relative shrink-0 size-[24px]" data-name="Cheveron">
        <div className="absolute bottom-[37.5%] left-1/4 right-1/4 top-[37.5%]">
          <div className="absolute inset-[-16.67%_-8.33%]">
            <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 8">
              <path d="M1 1L7 7L13 1" id="Vector 1" stroke="var(--stroke-0, #1A1D1F)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function SubNavItem2() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex items-start justify-between p-[12px] relative w-full">
        <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Contact Attendees</p>
        <IconRight1 />
      </div>
    </div>
  );
}

function SubMenuStack() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0 w-full" data-name="Sub menu (stack)">
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex items-center justify-between p-[12px] relative w-full">
            <Left6 />
            <div className="content-stretch flex gap-[12px] items-start relative shrink-0" data-name="Icon (right)/couple">
              <div className="relative shrink-0 size-[24px]" data-name="Cheveron">
                <div className="absolute bottom-[37.5%] flex items-center justify-center left-1/4 right-1/4 top-[37.5%]">
                  <div className="flex-none h-[6px] rotate-180 w-[12px]">
                    <div className="relative size-full">
                      <div className="absolute inset-[-16.67%_-8.33%]">
                        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 8">
                          <path d="M1 1L7 7L13 1" id="Vector 1" stroke="var(--stroke-0, #6F767E)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
        <div className="h-[48px] relative shrink-0 w-[36px]" data-name="Tree">
          <div className="absolute bg-[#efefef] h-[48px] left-[23px] rounded-tl-[2px] rounded-tr-[2px] top-0 w-[2px]" />
          <div className="absolute left-[24px] size-[12px] top-[12px]">
            <div className="absolute inset-[-8.33%]">
              <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
                <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
              </svg>
            </div>
          </div>
        </div>
        <SubNavItem />
      </div>
      <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
        <div className="h-[48px] relative shrink-0 w-[36px]" data-name="Tree">
          <div className="absolute bg-[#efefef] h-[48px] left-[23px] rounded-tl-[2px] rounded-tr-[2px] top-0 w-[2px]" />
          <div className="absolute left-[24px] size-[12px] top-[12px]">
            <div className="absolute inset-[-8.33%]">
              <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
                <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
              </svg>
            </div>
          </div>
        </div>
        <SubNavItem1 />
      </div>
      <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
        <div className="h-[48px] relative shrink-0 w-[36px]" data-name="Tree">
          <div className="absolute bg-[#efefef] h-[48px] left-[23px] rounded-tl-[2px] rounded-tr-[2px] top-0 w-[2px]" />
          <div className="absolute left-[24px] size-[12px] top-[12px]">
            <div className="absolute inset-[-8.33%]">
              <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
                <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
              </svg>
            </div>
          </div>
        </div>
        <SubNavItem2 />
      </div>
    </div>
  );
}

function Left7() {
  return (
    <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Left">
      <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/UI icon/pie_chart/light">
        <div className="absolute bottom-[8.33%] left-[8.33%] right-1/4 top-1/4" data-name="Ellipse 207 (Stroke)">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 16 16">
            <path clipRule="evenodd" d={svgPaths.p37d34000} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Ellipse 207 (Stroke)" />
          </svg>
        </div>
        <div className="absolute inset-[8.33%_8.33%_54.17%_54.17%]" data-name="Ellipse 208 (Stroke)">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 9 9">
            <path clipRule="evenodd" d={svgPaths.p9b9d700} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Ellipse 208 (Stroke)" />
          </svg>
        </div>
      </div>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">{`Sales & Reports`}</p>
    </div>
  );
}

function SubNavItem3() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex gap-[104px] items-start p-[12px] relative w-full">
        <p className="flex-[1_0_0] font-['Poppins:Medium',sans-serif] leading-[24px] min-h-px min-w-px not-italic relative text-[#353945] text-[14px]">Orders</p>
      </div>
    </div>
  );
}

function Tree() {
  return (
    <div className="relative self-stretch shrink-0 w-[36px]" data-name="Tree">
      <div className="absolute bg-[#efefef] h-[74px] left-[23px] rounded-tl-[2px] rounded-tr-[2px] top-[-0.48px] w-[2px]" />
      <div className="absolute left-[24px] size-[12px] top-[12px]">
        <div className="absolute inset-[-8.33%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
            <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function SubNavItem4() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex gap-[104px] items-start p-[12px] relative w-full">
        <p className="flex-[1_0_0] font-['Poppins:Medium',sans-serif] leading-[24px] min-h-px min-w-px not-italic relative text-[#353945] text-[14px]">Primary Sales</p>
      </div>
    </div>
  );
}

function SubMenu() {
  return (
    <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
      <Tree />
      <SubNavItem4 />
    </div>
  );
}

function IconRight2() {
  return (
    <div className="content-stretch flex gap-[12px] items-start opacity-0 relative shrink-0" data-name="Icon (right)">
      <div className="relative shrink-0 size-[24px]" data-name="Cheveron">
        <div className="absolute bottom-[37.5%] left-1/4 right-1/4 top-[37.5%]">
          <div className="absolute inset-[-16.67%_-8.33%]">
            <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 8">
              <path d="M1 1L7 7L13 1" id="Vector 1" stroke="var(--stroke-0, #1A1D1F)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function SubNavItem5() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex items-start justify-between p-[12px] relative w-full">
        <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Resales</p>
        <IconRight2 />
      </div>
    </div>
  );
}

function IconRight3() {
  return (
    <div className="content-stretch flex gap-[12px] items-start opacity-0 relative shrink-0" data-name="Icon (right)">
      <div className="relative shrink-0 size-[24px]" data-name="Cheveron">
        <div className="absolute bottom-[37.5%] left-1/4 right-1/4 top-[37.5%]">
          <div className="absolute inset-[-16.67%_-8.33%]">
            <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 8">
              <path d="M1 1L7 7L13 1" id="Vector 1" stroke="var(--stroke-0, #1A1D1F)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function SubNavItem6() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex items-start justify-between p-[12px] relative w-full">
        <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Daily ticket counts</p>
        <IconRight3 />
      </div>
    </div>
  );
}

function Left8() {
  return (
    <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Left">
      <div className="overflow-clip relative shrink-0 size-[24px]" data-name="Icons/icons/Megaphone/Line">
        <div className="absolute inset-[62.22%_58.33%_12.5%_17.77%]" data-name="Shape">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 5.73473 6.06714">
            <path d={svgPaths.p27938300} fill="var(--fill-0, #777E91)" id="Shape" />
          </svg>
        </div>
        <div className="absolute inset-[11.88%_8.33%_20.21%_4.17%]" data-name="Shape">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21 16.2995">
            <path clipRule="evenodd" d={svgPaths.p50f5700} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Shape" />
          </svg>
        </div>
        <div className="absolute inset-[26.74%_54.17%_35.08%_37.5%]" data-name="Shape">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 2 9.16324">
            <path d={svgPaths.p2a46ed00} fill="var(--fill-0, #777E91)" id="Shape" />
          </svg>
        </div>
        <div className="absolute inset-[37.86%_4.17%_46.19%_91.67%]" data-name="Shape">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 1 3.82929">
            <path d={svgPaths.p376cda00} fill="var(--fill-0, #777E91)" id="Shape" />
          </svg>
        </div>
      </div>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">Marketing</p>
    </div>
  );
}

function Tree1() {
  return (
    <div className="relative self-stretch shrink-0 w-[36px]" data-name="Tree">
      <div className="absolute bg-[#efefef] h-[74px] left-[23px] rounded-tl-[2px] rounded-tr-[2px] top-[-0.48px] w-[2px]" />
      <div className="absolute left-[24px] size-[12px] top-[12px]">
        <div className="absolute inset-[-8.33%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
            <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function SubNavItem7() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex gap-[104px] items-start p-[12px] relative w-full">
        <p className="flex-[1_0_0] font-['Poppins:Medium',sans-serif] leading-[24px] min-h-px min-w-px not-italic relative text-[#353945] text-[14px]">Tracking links</p>
      </div>
    </div>
  );
}

function SubMenu1() {
  return (
    <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
      <Tree1 />
      <SubNavItem7 />
    </div>
  );
}

function SubNavItem8() {
  return (
    <div className="flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]" data-name="Sub nav-item">
      <div className="content-stretch flex gap-[104px] items-start p-[12px] relative w-full">
        <p className="flex-[1_0_0] font-['Poppins:Medium',sans-serif] leading-[24px] min-h-px min-w-px not-italic relative text-[#353945] text-[14px]">Analytics</p>
      </div>
    </div>
  );
}

function Frame15() {
  return (
    <div className="content-stretch flex flex-col items-start pt-[8px] relative shrink-0 w-full">
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex items-center justify-between p-[12px] relative w-full">
            <Left8 />
            <div className="content-stretch flex gap-[12px] items-start relative shrink-0" data-name="Icon (right)/couple">
              <div className="relative shrink-0 size-[24px]" data-name="Cheveron">
                <div className="absolute bottom-[37.5%] flex items-center justify-center left-1/4 right-1/4 top-[37.5%]">
                  <div className="flex-none h-[6px] rotate-180 w-[12px]">
                    <div className="relative size-full">
                      <div className="absolute inset-[-16.67%_-8.33%]">
                        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 8">
                          <path d="M1 1L7 7L13 1" id="Vector 1" stroke="var(--stroke-0, #6F767E)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <SubMenu1 />
      <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
        <div className="h-[48px] relative shrink-0 w-[36px]" data-name="Tree">
          <div className="absolute bg-[#efefef] h-[16px] left-[23px] top-0 w-[2px]" />
          <div className="absolute left-[24px] size-[12px] top-[12px]">
            <div className="absolute inset-[-8.33%]">
              <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
                <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
              </svg>
            </div>
          </div>
        </div>
        <SubNavItem8 />
      </div>
    </div>
  );
}

function Frame14() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0 w-full">
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex items-center justify-between p-[12px] relative w-full">
            <Left7 />
            <div className="content-stretch flex gap-[12px] items-start relative shrink-0" data-name="Icon (right)/couple">
              <div className="relative shrink-0 size-[24px]" data-name="Cheveron">
                <div className="absolute bottom-[37.5%] flex items-center justify-center left-1/4 right-1/4 top-[37.5%]">
                  <div className="flex-none h-[6px] rotate-180 w-[12px]">
                    <div className="relative size-full">
                      <div className="absolute inset-[-16.67%_-8.33%]">
                        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 8">
                          <path d="M1 1L7 7L13 1" id="Vector 1" stroke="var(--stroke-0, #6F767E)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
        <div className="h-[48px] relative shrink-0 w-[36px]" data-name="Tree">
          <div className="absolute bg-[#efefef] h-[48px] left-[23px] rounded-tl-[2px] rounded-tr-[2px] top-0 w-[2px]" />
          <div className="absolute left-[24px] size-[12px] top-[12px]">
            <div className="absolute inset-[-8.33%]">
              <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
                <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
              </svg>
            </div>
          </div>
        </div>
        <SubNavItem3 />
      </div>
      <SubMenu />
      <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
        <div className="h-[48px] relative shrink-0 w-[36px]" data-name="Tree">
          <div className="absolute bg-[#efefef] h-[48px] left-[23px] rounded-tl-[2px] rounded-tr-[2px] top-0 w-[2px]" />
          <div className="absolute left-[24px] size-[12px] top-[12px]">
            <div className="absolute inset-[-8.33%]">
              <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
                <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
              </svg>
            </div>
          </div>
        </div>
        <SubNavItem5 />
      </div>
      <div className="content-stretch flex items-start relative rounded-[12px] shrink-0 w-full" data-name="Sub menu">
        <div className="h-[48px] relative shrink-0 w-[36px]" data-name="Tree">
          <div className="absolute bg-[#efefef] h-[48px] left-[23px] rounded-tl-[2px] rounded-tr-[2px] top-0 w-[2px]" />
          <div className="absolute left-[24px] size-[12px] top-[12px]">
            <div className="absolute inset-[-8.33%]">
              <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
                <path d={svgPaths.p1b456500} id="Vector 2" stroke="var(--stroke-0, #EFEFEF)" strokeLinecap="round" strokeWidth="2" />
              </svg>
            </div>
          </div>
        </div>
        <SubNavItem6 />
      </div>
      <Frame15 />
    </div>
  );
}

function NavStack() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0 w-full" data-name="Nav stack">
      <SubMenuStack />
      <Frame14 />
    </div>
  );
}

function TopElements() {
  return (
    <div className="content-stretch flex flex-col gap-[16px] items-center overflow-clip relative shrink-0 w-full" data-name="Top elements">
      <EventDetails />
      <Divider1 />
      <NavStack />
    </div>
  );
}

function Divider2() {
  return <div className="bg-[#f4f4f4] h-[2px] rounded-[2px] shrink-0 w-full" data-name="Divider" />;
}

function Left9() {
  return (
    <div className="content-stretch flex gap-[12px] items-center relative shrink-0" data-name="Left">
      <div className="overflow-clip relative shrink-0 size-[24px]" data-name="UI icon/help/light">
        <div className="absolute inset-[8.33%]" data-name="Ellipse 134 (Stroke)">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
            <path clipRule="evenodd" d={svgPaths.p3f44d800} fill="var(--fill-0, #6F767E)" fillRule="evenodd" id="Ellipse 134 (Stroke)" />
          </svg>
        </div>
        <div className="absolute inset-[70.83%_45.83%_20.83%_45.83%]">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 2 2">
            <circle cx="1" cy="1" fill="var(--fill-0, #6F767E)" id="Ellipse 190" r="1" />
          </svg>
        </div>
        <div className="absolute bottom-[33.33%] left-[34.04%] right-[33.33%] top-1/4" data-name="Ellipse 191 (Stroke)">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 7.82957 10">
            <path clipRule="evenodd" d={svgPaths.p38b4c9f0} fill="var(--fill-0, #6F767E)" fillRule="evenodd" id="Ellipse 191 (Stroke)" />
          </svg>
        </div>
      </div>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#6f767e] text-[14px] whitespace-nowrap">Support</p>
    </div>
  );
}

function Frame() {
  return (
    <div className="content-stretch flex flex-col gap-[16px] items-start relative shrink-0 w-full">
      <Divider2 />
      <div className="relative rounded-[12px] shrink-0 w-full" data-name="Nav item">
        <div className="flex flex-row items-center size-full">
          <div className="content-stretch flex gap-[12px] items-center p-[12px] relative w-full">
            <Left9 />
          </div>
        </div>
      </div>
    </div>
  );
}

function Bottom() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0 w-full" data-name="Bottom">
      <Frame />
    </div>
  );
}

function Tag() {
  return <div className="bg-[#3ea9f7] h-[32px] rounded-[4px] shrink-0 w-[16px]" data-name="tag" />;
}

function Title() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0" data-name="Title">
      <Tag />
      <p className="font-['Poppins:SemiBold',sans-serif] leading-[32px] not-italic relative shrink-0 text-[#1a1d1f] text-[24px] whitespace-nowrap">Dashboard</p>
    </div>
  );
}

function WidgetTitle1() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[377px] h-full items-center min-h-px min-w-px relative" data-name="Widget title">
      <Title />
    </div>
  );
}

function WidgetTitle() {
  return (
    <div className="content-stretch flex gap-[377px] h-[32px] items-center relative shrink-0 w-[690px]" data-name="Widget title">
      <div className="flex flex-[1_0_0] flex-row items-center self-stretch">
        <WidgetTitle1 />
      </div>
    </div>
  );
}

function Frame18() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0">
      <WidgetTitle />
    </div>
  );
}

function Frame89() {
  return (
    <div className="bg-white content-stretch flex gap-[8px] items-center px-[8px] py-[4px] relative rounded-[8px] shrink-0">
      <div className="overflow-clip relative shrink-0 size-[20px]" data-name="Icons/UI icon/repeat/light">
        <div className="absolute inset-[10.42%_21.7%_41.68%_12.5%]" data-name="Union">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.1595 9.58013">
            <path d={svgPaths.p2e369780} fill="var(--fill-0, #777E91)" id="Union" />
          </svg>
        </div>
        <div className="absolute inset-[41.67%_12.51%_10.43%_21.7%]" data-name="Union">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.1595 9.58008">
            <path d={svgPaths.p37857730} fill="var(--fill-0, #777E91)" id="Union" />
          </svg>
        </div>
      </div>
      <p className="font-['Poppins:Regular',sans-serif] leading-[20px] not-italic relative shrink-0 text-[#353945] text-[12px] whitespace-nowrap">Data refreshes automatically every 15 seconds</p>
    </div>
  );
}

function Frame19() {
  return (
    <div className="content-stretch flex items-center justify-between relative shrink-0 w-full">
      <Frame18 />
      <Frame89 />
    </div>
  );
}

function Frame69() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start leading-[0] not-italic relative shrink-0 text-center whitespace-nowrap">
      <div className="flex flex-col font-['Poppins:Bold',sans-serif] justify-center relative shrink-0 text-[#141416] text-[16px] uppercase">
        <p className="leading-[16px]">Seat Map</p>
      </div>
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center relative shrink-0 text-[#777e90] text-[14px]">
        <p className="leading-[1.7]">End stage 249</p>
      </div>
    </div>
  );
}

function Frame68() {
  return (
    <div className="content-stretch flex items-start relative shrink-0 w-full">
      <Frame69 />
    </div>
  );
}

function LageL() {
  return (
    <div className="absolute h-[10.442px] left-[43.47px] top-[34.54px] w-[21.005px]" data-name="Lage L">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21.0047 10.4419">
        <g id="Lage L">
          <path d={svgPaths.p19d21300} fill="var(--fill-0, white)" id="Lage L_2" />
        </g>
      </svg>
    </div>
  );
}

function LageCenter() {
  return (
    <div className="absolute h-[6.933px] left-[26.17px] top-[34.13px] w-[16.262px]" data-name="Lage Center">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 16.2617 6.93337">
        <g id="Lage Center">
          <path d={svgPaths.p3a40c800} fill="var(--fill-0, white)" id="Lage L" />
        </g>
      </svg>
    </div>
  );
}

function LageR() {
  return (
    <div className="absolute h-[10.403px] left-[4.65px] top-[34.58px] w-[20.525px]" data-name="Lage R">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.5248 10.4027">
        <g id="Lage R">
          <path d={svgPaths.p23e19300} fill="var(--fill-0, white)" id="Lage L" />
        </g>
      </svg>
    </div>
  );
}

function Lage() {
  return (
    <div className="absolute contents left-[4.65px] top-[34.13px]" data-name="Lage">
      <LageL />
      <LageCenter />
      <LageR />
    </div>
  );
}

function LinkedPathGroup() {
  return (
    <div className="absolute contents h-[3.436px] left-[43.88px] top-[82.29px] w-[17.395px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[44.05px] size-[0.924px] top-[82.37px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.78deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.74px] size-[0.924px] top-[83.33px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.8deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[52.06px] size-[0.951px] top-[83.35px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.51deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.37px] size-[0.978px] top-[83.42px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.35deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.12px] size-[1.006px] top-[83.34px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.31deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.03px] size-[1.032px] top-[83.71px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[8.14deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.33px] size-[1.054px] top-[83.88px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.85deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.63px] size-[1.074px] top-[84.13px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[11.43deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[60.1px] size-[1.094px] top-[84.62px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[13.01deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup1() {
  return (
    <div className="absolute contents h-[2.272px] left-[48.12px] top-[80.99px] w-[13.096px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[48.18px] size-[0.967px] top-[81.23px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-3.55deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[49.66px] size-[0.943px] top-[81.17px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-1.97deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[52.06px] size-[0.916px] top-[81.39px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.27deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[52.64px] size-[0.936px] top-[81.2px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[1.57deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.74px] size-[0.966px] top-[81.43px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[3.53deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.57px] size-[0.993px] top-[81.38px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[5.37deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.37px] size-[1.017px] top-[81.65px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.07deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.42px] size-[1.039px] top-[81.64px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[8.65deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[60.12px] size-[1.059px] top-[82.19px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[10.24deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup2() {
  return (
    <div className="absolute contents left-[49.33px] top-[79.21px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[49.33px] size-[1.004px] top-[79.53px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.7px] size-[0.981px] top-[79.46px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[52.05px] size-[0.955px] top-[79.38px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.4px] size-[0.927px] top-[79.35px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.15px] size-[0.927px] top-[79.21px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.05px] size-[0.955px] top-[79.34px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.36px] size-[0.981px] top-[79.42px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.68px] size-[1.004px] top-[79.52px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[59.9px] size-[1.026px] top-[79.59px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup3() {
  return (
    <div className="absolute contents left-[49.21px] top-[77.12px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[49.21px] size-[1.004px] top-[77.33px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.54px] size-[0.981px] top-[77.22px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.88px] size-[0.955px] top-[77.15px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.23px] size-[0.927px] top-[77.12px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.61px] size-[0.927px] top-[77.12px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.92px] size-[0.955px] top-[77.15px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.23px] size-[0.981px] top-[77.22px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.34px] size-[1.004px] top-[77.21px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[59.85px] size-[1.026px] top-[77.47px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup4() {
  return (
    <div className="absolute contents left-[49.12px] top-[74.76px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[49.12px] size-[1.004px] top-[75.12px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.46px] size-[0.981px] top-[75px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.79px] size-[0.955px] top-[74.93px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.14px] size-[0.927px] top-[74.9px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.89px] size-[0.927px] top-[74.76px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.83px] size-[0.955px] top-[74.93px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.14px] size-[0.981px] top-[75.01px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.25px] size-[1.004px] top-[74.99px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[59.76px] size-[1.026px] top-[75.26px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup5() {
  return (
    <div className="absolute contents left-[49.12px] top-[72.6px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[49.12px] size-[1.004px] top-[72.97px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.47px] size-[0.981px] top-[72.86px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.8px] size-[0.955px] top-[72.78px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.15px] size-[0.927px] top-[72.74px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.91px] size-[0.927px] top-[72.6px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.84px] size-[0.955px] top-[72.78px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.11px] size-[0.981px] top-[72.81px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.22px] size-[1.004px] top-[72.79px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[59.7px] size-[1.026px] top-[73.03px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup6() {
  return (
    <div className="absolute contents left-[48.89px] top-[70.98px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[48.89px] size-[1.004px] top-[71.19px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.26px] size-[0.981px] top-[71.08px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.62px] size-[0.955px] top-[71px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53px] size-[0.927px] top-[70.98px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.53px] size-[0.927px] top-[71.12px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.88px] size-[0.955px] top-[71.16px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.22px] size-[0.981px] top-[71.24px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.57px] size-[1.004px] top-[71.35px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[59.95px] size-[1.026px] top-[71.56px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup7() {
  return (
    <div className="absolute contents left-[48.98px] top-[68.86px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[48.97px] size-[1.004px] top-[69.09px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.33px] size-[0.981px] top-[68.98px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.7px] size-[0.955px] top-[68.9px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.08px] size-[0.927px] top-[68.87px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.47px] size-[0.927px] top-[68.86px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.81px] size-[0.955px] top-[68.9px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.88px] size-[0.981px] top-[68.89px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.33px] size-[1.004px] top-[69.01px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[59.77px] size-[1.026px] top-[69.18px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup8() {
  return (
    <div className="absolute contents left-[48.76px] top-[66.49px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[48.76px] size-[1.004px] top-[66.81px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.13px] size-[0.981px] top-[66.7px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.78px] size-[0.955px] top-[66.54px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[52.26px] size-[0.927px] top-[66.49px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.27px] size-[0.927px] top-[66.58px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.6px] size-[0.955px] top-[66.62px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.67px] size-[0.981px] top-[66.62px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.12px] size-[1.004px] top-[66.74px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[59.57px] size-[1.026px] top-[66.9px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup9() {
  return (
    <div className="absolute contents left-[48.13px] top-[64.3px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[48.13px] size-[1.004px] top-[64.63px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[49.49px] size-[0.981px] top-[64.52px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.87px] size-[0.955px] top-[64.44px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.63px] size-[0.927px] top-[64.3px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.63px] size-[0.927px] top-[64.41px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.98px] size-[0.955px] top-[64.44px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.05px] size-[0.981px] top-[64.43px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.5px] size-[1.004px] top-[64.56px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.93px] size-[1.026px] top-[64.71px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup10() {
  return (
    <div className="absolute contents left-[48.02px] top-[62.04px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[48.03px] size-[1.004px] top-[62.37px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[49.39px] size-[0.981px] top-[62.26px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.76px] size-[0.955px] top-[62.18px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.53px] size-[0.927px] top-[62.04px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.53px] size-[0.927px] top-[62.14px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.87px] size-[0.955px] top-[62.18px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.95px] size-[0.981px] top-[62.17px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.39px] size-[1.004px] top-[62.28px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.83px] size-[1.026px] top-[62.45px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup11() {
  return (
    <div className="absolute contents left-[48.02px] top-[59.81px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[48.02px] size-[1.004px] top-[60.14px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[49.39px] size-[0.981px] top-[60.02px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.04px] size-[0.955px] top-[59.86px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.52px] size-[0.927px] top-[59.81px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.53px] size-[0.927px] top-[59.91px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.86px] size-[0.955px] top-[59.95px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.93px] size-[0.981px] top-[59.94px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.38px] size-[1.004px] top-[60.05px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.83px] size-[1.026px] top-[60.22px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup12() {
  return (
    <div className="absolute contents left-[47.49px] top-[57.71px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[47.49px] size-[1.004px] top-[57.85px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[48.93px] size-[0.981px] top-[57.82px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.3px] size-[0.955px] top-[57.75px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.67px] size-[0.927px] top-[57.72px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.07px] size-[0.927px] top-[57.71px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.41px] size-[0.955px] top-[57.75px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.48px] size-[0.981px] top-[57.75px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.94px] size-[1.004px] top-[57.86px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.36px] size-[1.026px] top-[58.02px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup13() {
  return (
    <div className="absolute contents left-[47.26px] top-[55.39px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[47.26px] size-[1.004px] top-[55.72px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[48.62px] size-[0.981px] top-[55.61px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[49.27px] size-[0.955px] top-[55.44px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.75px] size-[0.927px] top-[55.39px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[52.76px] size-[0.927px] top-[55.49px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.1px] size-[0.955px] top-[55.53px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.18px] size-[0.981px] top-[55.53px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.62px] size-[1.004px] top-[55.64px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.06px] size-[1.026px] top-[55.8px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup14() {
  return (
    <div className="absolute contents left-[47.39px] top-[53.43px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[47.39px] size-[1.004px] top-[53.69px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[48.76px] size-[0.981px] top-[53.56px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.11px] size-[0.955px] top-[53.49px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[51.49px] size-[0.927px] top-[53.46px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[52.77px] size-[0.927px] top-[53.43px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[54.14px] size-[0.955px] top-[53.49px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.51px] size-[0.981px] top-[53.55px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.89px] size-[1.004px] top-[53.67px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[58.24px] size-[1.026px] top-[53.83px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup15() {
  return (
    <div className="absolute contents left-[46.7px] top-[51.11px]" data-name="Linked Path Group">
      <div className="absolute flex items-center justify-center left-[46.7px] size-[1.004px] top-[51.34px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[48.09px] size-[0.981px] top-[51.23px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[49.48px] size-[0.955px] top-[51.14px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[50.88px] size-[0.927px] top-[51.11px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[52.31px] size-[0.927px] top-[51.11px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[0.98deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[53.69px] size-[0.955px] top-[51.14px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.82deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[55.05px] size-[0.981px] top-[51.23px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.52deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[56.43px] size-[1.004px] top-[51.34px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.1deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex items-center justify-center left-[57.78px] size-[1.026px] top-[51.5px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.69deg]">
          <div className="relative size-[0.912px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function OrchLeft() {
  return (
    <div className="absolute contents left-[42.74px] top-[47.33px]" data-name="Orch Left">
      <div className="absolute flex h-[69.663px] items-center justify-center left-[42.75px] top-[47.33px] w-[21.731px]">
        <div className="-scale-y-100 flex-none rotate-180">
          <div className="h-[69.663px] relative w-[21.731px]" data-name="BG">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21.731 69.6627">
              <path d={svgPaths.p7bd55c0} fill="var(--fill-0, white)" id="BG" />
            </svg>
          </div>
        </div>
      </div>
      <LinkedPathGroup />
      <LinkedPathGroup1 />
      <LinkedPathGroup2 />
      <LinkedPathGroup3 />
      <LinkedPathGroup4 />
      <LinkedPathGroup5 />
      <LinkedPathGroup6 />
      <LinkedPathGroup7 />
      <LinkedPathGroup8 />
      <LinkedPathGroup9 />
      <LinkedPathGroup10 />
      <LinkedPathGroup11 />
      <LinkedPathGroup12 />
      <LinkedPathGroup13 />
      <LinkedPathGroup14 />
      <LinkedPathGroup15 />
    </div>
  );
}

function LinkedPathGroup16() {
  return (
    <div className="absolute contents inset-[88.02%_25.97%_8.98%_20.75%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[89.07%_74.95%_9.05%_20.76%] items-center justify-center">
        <div className="flex-none rotate-[-12.43deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[88.67%_69.65%_9.5%_26.18%] items-center justify-center">
        <div className="flex-none rotate-[-9.81deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[88.34%_64.3%_9.9%_31.68%] items-center justify-center">
        <div className="flex-none rotate-[-7.25deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[88.12%_58.96%_10.18%_37.17%] items-center justify-center">
        <div className="flex-none rotate-[-4.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[88.02%_53.58%_10.35%_42.72%] items-center justify-center">
        <div className="flex-none rotate-[-1.64deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[88.05%_47.97%_10.33%_48.32%] items-center justify-center">
        <div className="flex-none rotate-[1.64deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[88.13%_42.4%_10.17%_53.72%] items-center justify-center">
        <div className="flex-none rotate-[4.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[88.36%_36.93%_9.88%_59.05%] items-center justify-center">
        <div className="flex-none rotate-[7.25deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[88.67%_31.43%_9.51%_64.41%] items-center justify-center">
        <div className="flex-none rotate-[9.81deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[89.14%_25.97%_8.98%_69.74%] items-center justify-center">
        <div className="flex-none rotate-[12.47deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup17() {
  return (
    <div className="absolute contents inset-[84.23%_20.58%_12.23%_15.3%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[85.79%_80.27%_12.26%_15.3%] items-center justify-center">
        <div className="flex-none rotate-[-15.63deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute bottom-[12.88%] flex items-center justify-center left-[20.73%] right-3/4 top-[85.25%]">
        <div className="-rotate-12 flex-none size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[84.79%_69.73%_13.39%_26.12%] items-center justify-center">
        <div className="flex-none rotate-[-9.49deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[84.49%_64.37%_13.75%_31.62%] items-center justify-center">
        <div className="flex-none rotate-[-7.03deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[84.3%_58.96%_14%_37.17%] items-center justify-center">
        <div className="flex-none rotate-[-4.43deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[84.23%_53.61%_14.15%_42.69%] items-center justify-center">
        <div className="flex-none rotate-[-1.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[84.27%_48.03%_14.11%_48.27%] items-center justify-center">
        <div className="flex-none rotate-[1.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[84.37%_42.46%_13.93%_53.67%] items-center justify-center">
        <div className="flex-none rotate-[4.43deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[84.55%_36.95%_13.69%_59.03%] items-center justify-center">
        <div className="flex-none rotate-[7.03deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[84.85%_31.45%_13.33%_64.4%] items-center justify-center">
        <div className="flex-none rotate-[9.49deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[85.32%_26.02%_12.81%_69.7%] items-center justify-center">
        <div className="flex-none rotate-[12.03deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[85.82%_20.59%_12.23%_74.96%] items-center justify-center">
        <div className="flex-none rotate-[15.86deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup18() {
  return (
    <div className="absolute contents inset-[79.73%_20.46%_16.37%_14.02%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[80.99%_81.71%_17.13%_14.01%] items-center justify-center">
        <div className="flex-none rotate-[-12.14deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[80.57%_76.42%_17.6%_19.41%] items-center justify-center">
        <div className="flex-none rotate-[-9.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[80.24%_71.07%_17.99%_24.88%] items-center justify-center">
        <div className="flex-none rotate-[-7.85deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[79.93%_65.69%_18.34%_30.36%] items-center justify-center">
        <div className="flex-none rotate-[-5.82deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[79.77%_60.26%_18.56%_35.92%] items-center justify-center">
        <div className="flex-none rotate-[-3.67deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[79.73%_54.88%_18.65%_41.44%] items-center justify-center">
        <div className="flex-none rotate-[-1.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[80.47%_47.9%_17.92%_48.42%] items-center justify-center">
        <div className="flex-none rotate-[1.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[80.53%_42.35%_17.79%_53.83%] items-center justify-center">
        <div className="flex-none rotate-[3.67deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[80.69%_36.87%_17.58%_59.18%] items-center justify-center">
        <div className="flex-none rotate-[5.82deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[80.98%_31.36%_17.24%_64.58%] items-center justify-center">
        <div className="flex-none rotate-[7.88deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[81.31%_25.89%_16.86%_69.94%] items-center justify-center">
        <div className="flex-none rotate-[9.92deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[81.75%_20.46%_16.37%_75.26%] items-center justify-center">
        <div className="flex-none rotate-[12.2deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup19() {
  return (
    <div className="absolute contents inset-[76.67%_20.39%_20.14%_15.44%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[77.91%_80.29%_20.21%_15.43%] items-center justify-center">
        <div className="flex-none rotate-[-12.14deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[77.5%_74.97%_20.67%_20.86%] items-center justify-center">
        <div className="flex-none rotate-[-9.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[77.14%_69.62%_21.08%_26.32%] items-center justify-center">
        <div className="flex-none rotate-[-7.85deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.93%_64.24%_21.34%_31.82%] items-center justify-center">
        <div className="flex-none rotate-[-5.82deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.76%_58.87%_21.57%_37.31%] items-center justify-center">
        <div className="flex-none rotate-[-3.67deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.67%_53.43%_21.71%_42.89%] items-center justify-center">
        <div className="flex-none rotate-[-1.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.69%_47.83%_21.7%_48.49%] items-center justify-center">
        <div className="flex-none rotate-[1.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.78%_42.32%_21.55%_53.86%] items-center justify-center">
        <div className="flex-none rotate-[3.67deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.94%_36.78%_21.33%_59.28%] items-center justify-center">
        <div className="flex-none rotate-[5.82deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[77.21%_31.3%_21.01%_64.64%] items-center justify-center">
        <div className="flex-none rotate-[7.88deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[77.53%_25.83%_20.64%_70%] items-center justify-center">
        <div className="flex-none rotate-[9.92deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[77.98%_20.4%_20.14%_75.32%] items-center justify-center">
        <div className="flex-none rotate-[12.2deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup20() {
  return (
    <div className="absolute contents inset-[75.25%_12.86%_21.39%_12.14%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[76.71%_83.59%_21.42%_12.14%] items-center justify-center">
        <div className="flex-none rotate-[-11.92deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.27%_78.24%_21.9%_17.6%] items-center justify-center">
        <div className="flex-none rotate-[-9.79deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.93%_72.9%_22.28%_23.03%] items-center justify-center">
        <div className="flex-none rotate-[-8.09deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.61%_67.5%_22.65%_28.52%] items-center justify-center">
        <div className="flex-none rotate-[-6.45deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.41%_62.1%_22.88%_34.01%] items-center justify-center">
        <div className="flex-none rotate-[-4.77deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.29%_56.65%_23.05%_39.56%] items-center justify-center">
        <div className="flex-none rotate-[-2.99deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.25%_51.25%_23.14%_45.09%] items-center justify-center">
        <div className="flex-none rotate-[-1.06deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.28%_45.64%_23.12%_50.7%] items-center justify-center">
        <div className="flex-none rotate-[1.06deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.34%_40.09%_23.01%_56.13%] items-center justify-center">
        <div className="flex-none rotate-[2.99deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.44%_34.57%_22.86%_61.54%] items-center justify-center">
        <div className="flex-none rotate-[4.77deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.63%_29.06%_22.63%_66.96%] items-center justify-center">
        <div className="flex-none rotate-[6.45deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[75.97%_23.61%_22.24%_72.31%] items-center justify-center">
        <div className="flex-none rotate-[8.09deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.24%_18.39%_21.94%_77.45%] items-center justify-center">
        <div className="flex-none rotate-[9.82deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[76.74%_12.86%_21.39%_82.87%] items-center justify-center">
        <div className="flex-none rotate-[11.98deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup21() {
  return (
    <div className="absolute contents inset-[70.77%_11.66%_25.32%_10.03%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[72.3%_85.73%_25.84%_10.02%] items-center justify-center">
        <div className="flex-none rotate-[-11.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[71.81%_80.25%_26.37%_15.61%] items-center justify-center">
        <div className="flex-none rotate-[-9.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[71.51%_74.75%_26.71%_21.19%] items-center justify-center">
        <div className="flex-none rotate-[-7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[71.21%_69.19%_27.05%_26.84%] items-center justify-center">
        <div className="flex-none rotate-[-6.26deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[71%_63.61%_27.3%_32.51%] items-center justify-center">
        <div className="flex-none rotate-[-4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[70.83%_58%_27.52%_38.22%] items-center justify-center">
        <div className="flex-none rotate-[-2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[70.77%_52.44%_27.62%_43.9%] items-center justify-center">
        <div className="flex-none rotate-[-1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[70.79%_46.64%_27.6%_49.69%] items-center justify-center">
        <div className="flex-none rotate-[1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[70.87%_40.99%_27.48%_55.23%] items-center justify-center">
        <div className="flex-none rotate-[2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[71%_35.3%_27.3%_60.82%] items-center justify-center">
        <div className="flex-none rotate-[4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[71.2%_29.63%_27.05%_66.39%] items-center justify-center">
        <div className="flex-none rotate-[6.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[71.53%_24%_26.69%_71.94%] items-center justify-center">
        <div className="flex-none rotate-[7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[71.87%_18.37%_26.32%_77.48%] items-center justify-center">
        <div className="flex-none rotate-[9.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[72.81%_11.67%_25.32%_84.08%] items-center justify-center">
        <div className="flex-none rotate-[11.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup22() {
  return (
    <div className="absolute contents inset-[66.98%_11.5%_28.86%_9.63%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[68.45%_86.16%_29.69%_9.62%] items-center justify-center">
        <div className="flex-none rotate-[-11.15deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.99%_80.64%_30.2%_15.23%] items-center justify-center">
        <div className="flex-none rotate-[-9.27deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.64%_75.12%_30.59%_20.83%] items-center justify-center">
        <div className="flex-none rotate-[-7.66deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.37%_69.61%_30.9%_26.43%] items-center justify-center">
        <div className="flex-none rotate-[-6.1deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.17%_64.02%_31.13%_32.1%] items-center justify-center">
        <div className="flex-none rotate-[-4.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.04%_58.45%_31.3%_37.78%] items-center justify-center">
        <div className="flex-none rotate-[-2.82deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[66.99%_52.88%_31.4%_43.46%] items-center justify-center">
        <div className="flex-none rotate-[-0.98deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[66.98%_47.08%_31.42%_49.26%] items-center justify-center">
        <div className="flex-none rotate-[0.98deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.04%_41.35%_31.31%_54.88%] items-center justify-center">
        <div className="flex-none rotate-[2.82deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.2%_35.68%_31.11%_60.45%] items-center justify-center">
        <div className="flex-none rotate-[4.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.41%_30.01%_30.86%_66.03%] items-center justify-center">
        <div className="flex-none rotate-[6.1deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[67.69%_24.41%_30.54%_71.54%] items-center justify-center">
        <div className="flex-none rotate-[7.69deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[68.26%_18.22%_29.92%_77.64%] items-center justify-center">
        <div className="flex-none rotate-[9.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[69.29%_11.52%_28.86%_84.25%] items-center justify-center">
        <div className="flex-none rotate-[11.19deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup23() {
  return (
    <div className="absolute contents inset-[49.54%_11.64%_33.03%_-5.81%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[64.6%_85.71%_33.54%_10.04%] items-center justify-center">
        <div className="flex-none rotate-[-11.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[64.14%_80.23%_34.04%_15.62%] items-center justify-center">
        <div className="flex-none rotate-[-9.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[49.54%_101.76%_48.68%_-5.82%] items-center justify-center">
        <div className="flex-none rotate-[-7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.5%_69.14%_34.76%_26.88%] items-center justify-center">
        <div className="flex-none rotate-[-6.26deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.29%_63.56%_35.01%_32.56%] items-center justify-center">
        <div className="flex-none rotate-[-4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.14%_58.02%_35.2%_38.21%] items-center justify-center">
        <div className="flex-none rotate-[-2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.06%_52.45%_35.33%_43.88%] items-center justify-center">
        <div className="flex-none rotate-[-1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.09%_46.69%_35.3%_49.65%] items-center justify-center">
        <div className="flex-none rotate-[1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.16%_40.95%_35.19%_55.27%] items-center justify-center">
        <div className="flex-none rotate-[2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.29%_35.28%_35.01%_60.84%] items-center justify-center">
        <div className="flex-none rotate-[4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.51%_29.62%_34.74%_66.41%] items-center justify-center">
        <div className="flex-none rotate-[6.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[63.82%_24.01%_34.4%_71.92%] items-center justify-center">
        <div className="flex-none rotate-[7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[64.17%_18.35%_34.01%_77.5%] items-center justify-center">
        <div className="flex-none rotate-[9.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[65.1%_11.65%_33.03%_84.1%] items-center justify-center">
        <div className="flex-none rotate-[11.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup24() {
  return (
    <div className="absolute contents inset-[59.15%_11.64%_36.92%_10.05%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[60.69%_85.71%_37.45%_10.04%] items-center justify-center">
        <div className="flex-none rotate-[-11.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[60.21%_80.23%_37.98%_15.62%] items-center justify-center">
        <div className="flex-none rotate-[-9.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.9%_74.7%_38.32%_21.24%] items-center justify-center">
        <div className="flex-none rotate-[-7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.6%_69.14%_38.66%_26.88%] items-center justify-center">
        <div className="flex-none rotate-[-6.26deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.37%_63.56%_38.93%_32.56%] items-center justify-center">
        <div className="flex-none rotate-[-4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.24%_58.02%_39.11%_38.21%] items-center justify-center">
        <div className="flex-none rotate-[-2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.15%_52.45%_39.24%_43.88%] items-center justify-center">
        <div className="flex-none rotate-[-1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.18%_46.69%_39.21%_49.65%] items-center justify-center">
        <div className="flex-none rotate-[1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.24%_41.01%_39.1%_55.21%] items-center justify-center">
        <div className="flex-none rotate-[2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.38%_35.28%_38.92%_60.84%] items-center justify-center">
        <div className="flex-none rotate-[4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.59%_29.65%_38.67%_66.38%] items-center justify-center">
        <div className="flex-none rotate-[6.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[59.91%_24.01%_38.31%_71.92%] items-center justify-center">
        <div className="flex-none rotate-[7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[60.27%_18.42%_37.91%_77.44%] items-center justify-center">
        <div className="flex-none rotate-[9.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[61.22%_11.65%_36.92%_84.1%] items-center justify-center">
        <div className="flex-none rotate-[11.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup25() {
  return (
    <div className="absolute contents inset-[55.15%_11.63%_40.92%_10.07%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[56.69%_85.7%_41.45%_10.06%] items-center justify-center">
        <div className="flex-none rotate-[-11.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[56.2%_80.21%_41.98%_15.64%] items-center justify-center">
        <div className="flex-none rotate-[-9.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.9%_74.68%_42.32%_21.26%] items-center justify-center">
        <div className="flex-none rotate-[-7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.6%_69.13%_42.66%_26.9%] items-center justify-center">
        <div className="flex-none rotate-[-6.26deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.37%_63.54%_42.93%_32.58%] items-center justify-center">
        <div className="flex-none rotate-[-4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.24%_57.97%_43.1%_38.25%] items-center justify-center">
        <div className="flex-none rotate-[-2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.15%_52.4%_43.24%_43.93%] items-center justify-center">
        <div className="flex-none rotate-[-1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.18%_46.64%_43.21%_49.7%] items-center justify-center">
        <div className="flex-none rotate-[1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.24%_40.99%_43.1%_55.23%] items-center justify-center">
        <div className="flex-none rotate-[2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.38%_35.27%_42.92%_60.85%] items-center justify-center">
        <div className="flex-none rotate-[4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.59%_29.62%_42.67%_66.41%] items-center justify-center">
        <div className="flex-none rotate-[6.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[55.9%_23.97%_42.32%_71.97%] items-center justify-center">
        <div className="flex-none rotate-[7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[56.27%_18.37%_41.91%_77.48%] items-center justify-center">
        <div className="flex-none rotate-[9.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[57.22%_11.64%_40.92%_84.12%] items-center justify-center">
        <div className="flex-none rotate-[11.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup26() {
  return (
    <div className="absolute contents inset-[52.59%_9.3%_43.43%_10.32%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[54.18%_85.44%_43.96%_10.31%] items-center justify-center">
        <div className="flex-none rotate-[-11.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[53.7%_79.8%_44.49%_16.05%] items-center justify-center">
        <div className="flex-none rotate-[-9.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[53.35%_74.12%_44.87%_21.82%] items-center justify-center">
        <div className="flex-none rotate-[-7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[53.06%_68.41%_45.2%_27.62%] items-center justify-center">
        <div className="flex-none rotate-[-6.26deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[52.81%_62.67%_45.48%_33.45%] items-center justify-center">
        <div className="flex-none rotate-[-4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[52.69%_56.94%_45.66%_39.28%] items-center justify-center">
        <div className="flex-none rotate-[-2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[52.59%_51.19%_45.8%_45.14%] items-center justify-center">
        <div className="flex-none rotate-[-1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[52.61%_45.3%_45.78%_51.03%] items-center justify-center">
        <div className="flex-none rotate-[1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[52.67%_39.42%_45.67%_56.81%] items-center justify-center">
        <div className="flex-none rotate-[2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[52.81%_33.59%_45.49%_62.53%] items-center justify-center">
        <div className="flex-none rotate-[4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[53.06%_27.77%_45.2%_68.25%] items-center justify-center">
        <div className="flex-none rotate-[6.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[53.37%_21.97%_44.85%_73.97%] items-center justify-center">
        <div className="flex-none rotate-[7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[53.73%_16.2%_44.46%_79.65%] items-center justify-center">
        <div className="flex-none rotate-[9.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[54.71%_9.31%_43.43%_86.44%] items-center justify-center">
        <div className="flex-none rotate-[11.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup27() {
  return (
    <div className="absolute contents inset-[48.55%_9.31%_47.49%_10.32%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[50.11%_85.45%_48.03%_10.31%] items-center justify-center">
        <div className="flex-none rotate-[-11.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[49.64%_79.78%_48.54%_16.08%] items-center justify-center">
        <div className="flex-none rotate-[-9.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[49.3%_74.1%_48.92%_21.84%] items-center justify-center">
        <div className="flex-none rotate-[-7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[49%_68.38%_49.25%_27.64%] items-center justify-center">
        <div className="flex-none rotate-[-6.26deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[48.76%_62.67%_49.53%_33.45%] items-center justify-center">
        <div className="flex-none rotate-[-4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[48.62%_56.92%_49.73%_39.31%] items-center justify-center">
        <div className="flex-none rotate-[-2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[48.55%_51.17%_49.85%_45.17%] items-center justify-center">
        <div className="flex-none rotate-[-1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[48.55%_45.25%_49.84%_51.09%] items-center justify-center">
        <div className="flex-none rotate-[1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[48.62%_39.39%_49.72%_56.83%] items-center justify-center">
        <div className="flex-none rotate-[2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[48.76%_33.57%_49.54%_62.55%] items-center justify-center">
        <div className="flex-none rotate-[4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[49%_27.75%_49.26%_68.28%] items-center justify-center">
        <div className="flex-none rotate-[6.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[49.28%_21.96%_48.94%_73.98%] items-center justify-center">
        <div className="flex-none rotate-[7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[49.64%_16.21%_48.55%_79.65%] items-center justify-center">
        <div className="flex-none rotate-[9.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[50.64%_9.32%_47.49%_86.43%] items-center justify-center">
        <div className="flex-none rotate-[11.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup28() {
  return (
    <div className="absolute contents inset-[44.58%_9.27%_51.43%_10.33%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[46.14%_85.43%_52%_10.32%] items-center justify-center">
        <div className="flex-none rotate-[-11.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[45.67%_79.8%_52.51%_16.06%] items-center justify-center">
        <div className="flex-none rotate-[-9.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[45.33%_74.08%_52.89%_21.86%] items-center justify-center">
        <div className="flex-none rotate-[-7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[45.04%_68.37%_53.22%_27.66%] items-center justify-center">
        <div className="flex-none rotate-[-6.26deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[44.8%_62.67%_53.5%_33.46%] items-center justify-center">
        <div className="flex-none rotate-[-4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[44.65%_56.94%_53.7%_39.29%] items-center justify-center">
        <div className="flex-none rotate-[-2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[44.58%_51.18%_53.81%_45.16%] items-center justify-center">
        <div className="flex-none rotate-[-1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[44.59%_45.24%_53.81%_51.1%] items-center justify-center">
        <div className="flex-none rotate-[1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[44.65%_39.41%_53.7%_56.81%] items-center justify-center">
        <div className="flex-none rotate-[2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[44.79%_33.59%_53.51%_62.53%] items-center justify-center">
        <div className="flex-none rotate-[4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[45.04%_27.74%_53.22%_68.29%] items-center justify-center">
        <div className="flex-none rotate-[6.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[45.34%_21.97%_52.88%_73.97%] items-center justify-center">
        <div className="flex-none rotate-[7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[45.7%_16.19%_52.48%_79.66%] items-center justify-center">
        <div className="flex-none rotate-[9.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[46.7%_9.28%_51.43%_86.47%] items-center justify-center">
        <div className="flex-none rotate-[11.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup29() {
  return (
    <div className="absolute contents inset-[40.39%_9.28%_55.63%_10.31%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[41.94%_85.45%_56.19%_10.3%] items-center justify-center">
        <div className="flex-none rotate-[-11.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[41.48%_79.81%_56.7%_16.04%] items-center justify-center">
        <div className="flex-none rotate-[-9.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[41.14%_74.1%_57.08%_21.84%] items-center justify-center">
        <div className="flex-none rotate-[-7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[40.84%_68.39%_57.42%_27.64%] items-center justify-center">
        <div className="flex-none rotate-[-6.26deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[40.6%_62.7%_57.7%_33.42%] items-center justify-center">
        <div className="flex-none rotate-[-4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[40.45%_56.97%_57.89%_39.25%] items-center justify-center">
        <div className="flex-none rotate-[-2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[40.39%_51.17%_58%_45.16%] items-center justify-center">
        <div className="flex-none rotate-[-1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[40.39%_45.27%_58%_51.06%] items-center justify-center">
        <div className="flex-none rotate-[1.04deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[40.46%_39.45%_57.88%_56.77%] items-center justify-center">
        <div className="flex-none rotate-[2.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[40.6%_33.6%_57.7%_62.52%] items-center justify-center">
        <div className="flex-none rotate-[4.62deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[40.85%_27.75%_57.41%_68.27%] items-center justify-center">
        <div className="flex-none rotate-[6.29deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[41.15%_21.98%_57.07%_73.95%] items-center justify-center">
        <div className="flex-none rotate-[7.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[41.51%_16.21%_56.67%_79.64%] items-center justify-center">
        <div className="flex-none rotate-[9.55deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[42.51%_9.29%_55.63%_86.46%] items-center justify-center">
        <div className="flex-none rotate-[11.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup30() {
  return (
    <div className="absolute contents inset-[36.63%_15%_59.62%_16.19%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[37.87%_79.59%_60.28%_16.19%] items-center justify-center">
        <div className="flex-none rotate-[-11.02deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[37.49%_73.92%_60.7%_21.96%] items-center justify-center">
        <div className="flex-none rotate-[-9.05deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[37.09%_68.28%_61.15%_27.7%] items-center justify-center">
        <div className="flex-none rotate-[-7.21deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[36.88%_62.52%_61.4%_33.56%] items-center justify-center">
        <div className="flex-none rotate-[-5.31deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[36.74%_56.81%_61.59%_39.39%] items-center justify-center">
        <div className="flex-none rotate-[-3.31deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[36.63%_51.11%_61.76%_45.22%] items-center justify-center">
        <div className="flex-none rotate-[-1.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[36.65%_45.2%_61.74%_51.13%] items-center justify-center">
        <div className="flex-none rotate-[1.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[36.69%_39.28%_61.64%_56.92%] items-center justify-center">
        <div className="flex-none rotate-[3.31deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[36.92%_33.44%_61.36%_62.64%] items-center justify-center">
        <div className="flex-none rotate-[5.31deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[37.16%_27.66%_61.08%_68.32%] items-center justify-center">
        <div className="flex-none rotate-[7.21deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[37.44%_21.86%_60.75%_74.02%] items-center justify-center">
        <div className="flex-none rotate-[9.05deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[38.53%_14.98%_59.62%_80.79%] items-center justify-center">
        <div className="flex-none rotate-[11.05deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup31() {
  return (
    <div className="absolute contents inset-[32.48%_15.34%_63.59%_15.87%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[33.87%_79.8%_64.24%_15.88%] items-center justify-center">
        <div className="flex-none rotate-[-13.02deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[33.4%_74.15%_64.76%_21.65%] items-center justify-center">
        <div className="flex-none rotate-[-10.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[32.99%_68.46%_65.22%_27.45%] items-center justify-center">
        <div className="flex-none rotate-[-8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[32.76%_62.84%_65.5%_33.19%] items-center justify-center">
        <div className="flex-none rotate-[-6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[32.57%_57.11%_65.75%_39.05%] items-center justify-center">
        <div className="flex-none rotate-[-3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[32.5%_51.38%_65.89%_44.93%] items-center justify-center">
        <div className="flex-none rotate-[-1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[32.48%_45.42%_65.9%_50.89%] items-center justify-center">
        <div className="flex-none rotate-[1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[32.59%_39.59%_65.73%_56.58%] items-center justify-center">
        <div className="flex-none rotate-[3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[32.74%_33.72%_65.52%_62.32%] items-center justify-center">
        <div className="flex-none rotate-[6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[33.02%_27.9%_65.19%_68.01%] items-center justify-center">
        <div className="flex-none rotate-[8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[33.46%_22.18%_64.7%_73.62%] items-center justify-center">
        <div className="flex-none rotate-[10.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[34.51%_15.33%_63.59%_80.35%] items-center justify-center">
        <div className="flex-none rotate-[13.07deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup32() {
  return (
    <div className="absolute contents inset-[28.42%_15.34%_67.66%_15.97%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[29.8%_79.71%_68.31%_15.97%] items-center justify-center">
        <div className="flex-none rotate-[-13.02deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[29.33%_74.13%_68.83%_21.67%] items-center justify-center">
        <div className="flex-none rotate-[-10.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[28.92%_68.44%_69.29%_27.47%] items-center justify-center">
        <div className="flex-none rotate-[-8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[28.67%_62.82%_69.59%_33.21%] items-center justify-center">
        <div className="flex-none rotate-[-6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[28.5%_57.09%_69.82%_39.07%] items-center justify-center">
        <div className="flex-none rotate-[-3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[28.43%_51.38%_69.95%_44.93%] items-center justify-center">
        <div className="flex-none rotate-[-1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[28.42%_45.42%_69.97%_50.89%] items-center justify-center">
        <div className="flex-none rotate-[1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[28.51%_39.57%_69.81%_56.6%] items-center justify-center">
        <div className="flex-none rotate-[3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[28.68%_33.72%_69.58%_62.32%] items-center justify-center">
        <div className="flex-none rotate-[6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[28.96%_27.9%_69.25%_68.01%] items-center justify-center">
        <div className="flex-none rotate-[8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[29.36%_22.16%_68.8%_73.64%] items-center justify-center">
        <div className="flex-none rotate-[10.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[30.45%_15.33%_67.66%_80.35%] items-center justify-center">
        <div className="flex-none rotate-[13.07deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup33() {
  return (
    <div className="absolute contents inset-[24.35%_15.34%_71.72%_15.94%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[25.72%_79.74%_72.39%_15.95%] items-center justify-center">
        <div className="flex-none rotate-[-13.02deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[25.27%_74.12%_72.89%_21.68%] items-center justify-center">
        <div className="flex-none rotate-[-10.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[24.85%_68.46%_73.36%_27.45%] items-center justify-center">
        <div className="flex-none rotate-[-8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[24.6%_62.79%_73.66%_33.24%] items-center justify-center">
        <div className="flex-none rotate-[-6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[24.41%_57.11%_73.9%_39.05%] items-center justify-center">
        <div className="flex-none rotate-[-3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[24.35%_51.4%_74.04%_44.91%] items-center justify-center">
        <div className="flex-none rotate-[-1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[24.35%_45.44%_74.04%_50.87%] items-center justify-center">
        <div className="flex-none rotate-[1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[24.43%_39.59%_73.89%_56.58%] items-center justify-center">
        <div className="flex-none rotate-[3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[24.62%_33.71%_73.64%_62.33%] items-center justify-center">
        <div className="flex-none rotate-[6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[24.89%_27.92%_73.32%_67.99%] items-center justify-center">
        <div className="flex-none rotate-[8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[25.29%_22.18%_72.87%_73.62%] items-center justify-center">
        <div className="flex-none rotate-[10.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[26.38%_15.33%_71.72%_80.35%] items-center justify-center">
        <div className="flex-none rotate-[13.07deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup34() {
  return (
    <div className="absolute contents inset-[20.3%_15.34%_75.77%_15.97%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[21.68%_79.71%_76.43%_15.97%] items-center justify-center">
        <div className="flex-none rotate-[-13.02deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[21.22%_74.12%_76.94%_21.68%] items-center justify-center">
        <div className="flex-none rotate-[-10.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[20.81%_68.46%_77.4%_27.45%] items-center justify-center">
        <div className="flex-none rotate-[-8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[20.56%_62.81%_77.7%_33.22%] items-center justify-center">
        <div className="flex-none rotate-[-6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[20.38%_57.11%_77.93%_39.05%] items-center justify-center">
        <div className="flex-none rotate-[-3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[20.3%_51.4%_78.08%_44.91%] items-center justify-center">
        <div className="flex-none rotate-[-1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[20.3%_45.44%_78.08%_50.87%] items-center justify-center">
        <div className="flex-none rotate-[1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[20.38%_39.56%_77.93%_56.61%] items-center justify-center">
        <div className="flex-none rotate-[3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[20.56%_33.71%_77.7%_62.33%] items-center justify-center">
        <div className="flex-none rotate-[6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[20.84%_27.92%_77.37%_67.99%] items-center justify-center">
        <div className="flex-none rotate-[8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[21.24%_22.16%_76.92%_73.64%] items-center justify-center">
        <div className="flex-none rotate-[10.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[22.34%_15.33%_75.77%_80.35%] items-center justify-center">
        <div className="flex-none rotate-[13.07deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup35() {
  return (
    <div className="absolute contents inset-[16.21%_15.34%_79.87%_15.9%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[17.57%_79.77%_80.54%_15.91%] items-center justify-center">
        <div className="flex-none rotate-[-13.02deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[17.12%_74.12%_81.04%_21.68%] items-center justify-center">
        <div className="flex-none rotate-[-10.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[16.7%_68.46%_81.51%_27.45%] items-center justify-center">
        <div className="flex-none rotate-[-8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[16.45%_62.84%_81.81%_33.19%] items-center justify-center">
        <div className="flex-none rotate-[-6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[16.28%_57.11%_82.04%_39.05%] items-center justify-center">
        <div className="flex-none rotate-[-3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[16.21%_51.4%_82.17%_44.91%] items-center justify-center">
        <div className="flex-none rotate-[-1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[16.23%_45.44%_82.16%_50.87%] items-center justify-center">
        <div className="flex-none rotate-[1.39deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[16.29%_39.57%_82.03%_56.6%] items-center justify-center">
        <div className="flex-none rotate-[3.89deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[16.45%_33.74%_81.81%_62.29%] items-center justify-center">
        <div className="flex-none rotate-[6.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[16.74%_27.96%_81.47%_67.96%] items-center justify-center">
        <div className="flex-none rotate-[8.36deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[17.13%_22.16%_81.03%_73.64%] items-center justify-center">
        <div className="flex-none rotate-[10.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[18.23%_15.33%_79.88%_80.35%] items-center justify-center">
        <div className="flex-none rotate-[13.07deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup36() {
  return (
    <div className="absolute contents inset-[12.15%_14.98%_83.75%_16.3%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[13.79%_79.3%_84.28%_16.3%] items-center justify-center">
        <div className="flex-none rotate-[-14.76deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[13.2%_73.71%_84.93%_22.04%] items-center justify-center">
        <div className="flex-none rotate-[-11.61deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[12.8%_68.06%_85.39%_27.81%] items-center justify-center">
        <div className="flex-none rotate-[-9.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[12.44%_62.36%_85.81%_33.64%] items-center justify-center">
        <div className="flex-none rotate-[-6.77deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[12.23%_56.68%_86.08%_39.46%] items-center justify-center">
        <div className="flex-none rotate-[-4.25deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[12.15%_51.01%_86.23%_45.29%] items-center justify-center">
        <div className="flex-none rotate-[-1.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[12.15%_45.06%_86.23%_51.24%] items-center justify-center">
        <div className="flex-none rotate-[1.53deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[12.26%_39.17%_86.05%_56.97%] items-center justify-center">
        <div className="flex-none rotate-[4.3deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[12.47%_33.36%_85.78%_62.64%] items-center justify-center">
        <div className="flex-none rotate-[6.82deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[12.76%_27.55%_85.43%_68.32%] items-center justify-center">
        <div className="flex-none rotate-[9.18deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[13.21%_21.8%_84.93%_73.94%] items-center justify-center">
        <div className="flex-none rotate-[11.64deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[14.32%_14.97%_83.75%_80.63%] items-center justify-center">
        <div className="flex-none rotate-[14.86deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup37() {
  return (
    <div className="absolute contents inset-[8.1%_20.71%_88.28%_22%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[9.25%_73.71%_88.87%_22%] items-center justify-center">
        <div className="flex-none rotate-[-12.43deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[8.78%_68.07%_89.4%_27.77%] items-center justify-center">
        <div className="flex-none rotate-[-9.81deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[8.42%_62.41%_89.81%_33.57%] items-center justify-center">
        <div className="flex-none rotate-[-7.25deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[8.2%_56.69%_90.1%_39.43%] items-center justify-center">
        <div className="flex-none rotate-[-4.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[8.11%_51.01%_90.27%_45.29%] items-center justify-center">
        <div className="flex-none rotate-[-1.64deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[8.11%_45.12%_90.27%_51.17%] items-center justify-center">
        <div className="flex-none rotate-[1.64deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[8.22%_39.24%_90.08%_56.88%] items-center justify-center">
        <div className="flex-none rotate-[4.56deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[8.44%_33.4%_89.8%_62.58%] items-center justify-center">
        <div className="flex-none rotate-[7.25deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[8.75%_27.56%_89.42%_68.28%] items-center justify-center">
        <div className="flex-none rotate-[9.81deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[9.84%_20.71%_88.28%_74.99%] items-center justify-center">
        <div className="flex-none rotate-[12.47deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup38() {
  return (
    <div className="absolute contents inset-[3.82%_26.49%_93.03%_27.77%]" data-name="Linked Path Group">
      <div className="absolute flex inset-[4.53%_68.03%_93.63%_27.77%] items-center justify-center">
        <div className="flex-none rotate-[-10.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911787 0.911787">
              <path d={svgPaths.p2c71edb0} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[4.19%_62.37%_94.03%_33.57%] items-center justify-center">
        <div className="flex-none rotate-[-7.75deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[3.95%_56.73%_94.34%_39.37%] items-center justify-center">
        <div className="flex-none rotate-[-4.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[3.85%_50.99%_94.52%_45.3%] items-center justify-center">
        <div className="flex-none rotate-[-1.77deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[3.82%_45.09%_94.55%_51.2%] items-center justify-center">
        <div className="flex-none rotate-[1.77deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.pb18a500} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[3.93%_39.21%_94.36%_56.9%] items-center justify-center">
        <div className="flex-none rotate-[4.9deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[4.2%_33.37%_94.03%_62.57%] items-center justify-center">
        <div className="flex-none rotate-[7.79deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p11f01a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="absolute flex inset-[5.13%_26.48%_93.03%_69.32%] items-center justify-center">
        <div className="flex-none rotate-[10.52deg] size-[0.912px]">
          <div className="relative size-full" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.911786 0.911786">
              <path d={svgPaths.p25b95100} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function OrchCenter() {
  return (
    <div className="absolute h-[57.767px] left-[21.87px] top-[54.96px] w-[25.324px]" data-name="Orch Center">
      <div className="absolute inset-[0.05%_0.02%_-0.05%_-0.02%]" data-name="BG">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 25.3244 57.767">
          <path d={svgPaths.p7646f00} fill="var(--fill-0, white)" id="BG" />
        </svg>
      </div>
      <LinkedPathGroup16 />
      <LinkedPathGroup17 />
      <LinkedPathGroup18 />
      <LinkedPathGroup19 />
      <LinkedPathGroup20 />
      <LinkedPathGroup21 />
      <LinkedPathGroup22 />
      <LinkedPathGroup23 />
      <LinkedPathGroup24 />
      <LinkedPathGroup25 />
      <LinkedPathGroup26 />
      <LinkedPathGroup27 />
      <LinkedPathGroup28 />
      <LinkedPathGroup29 />
      <LinkedPathGroup30 />
      <LinkedPathGroup31 />
      <LinkedPathGroup32 />
      <LinkedPathGroup33 />
      <LinkedPathGroup34 />
      <LinkedPathGroup35 />
      <LinkedPathGroup36 />
      <LinkedPathGroup37 />
      <LinkedPathGroup38 />
    </div>
  );
}

function OrchRight() {
  return (
    <div className="absolute h-[69.945px] left-[4.68px] top-[47.3px] w-[21.731px]" data-name="Orch Right">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21.731 69.945">
        <g id="Orch Right">
          <path d={svgPaths.p2c537a80} fill="var(--fill-0, white)" id="BG" />
        </g>
      </svg>
    </div>
  );
}

function Orchestra() {
  return (
    <div className="absolute contents left-[4.68px] top-[47.3px]" data-name="Orchestra">
      <OrchLeft />
      <OrchCenter />
      <OrchRight />
    </div>
  );
}

function Scene() {
  return (
    <div className="absolute h-[20.241px] left-[14.54px] top-[112.68px] w-[39.978px]" data-name="Scene">
      <div className="absolute inset-[-0.84%_-0.42%_0_-0.42%]">
        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 40.3163 20.4105">
          <g id="Scene">
            <g id="Scene BG" />
            <path d={svgPaths.p38b3a060} id="Scene BG_2" stroke="var(--stroke-0, #B1B5C4)" strokeLinecap="round" strokeWidth="0.338782" />
          </g>
        </svg>
      </div>
    </div>
  );
}

function BalconyRight() {
  return (
    <div className="absolute h-[28.455px] left-[4.65px] top-[5.69px] w-[20.525px]" data-name="Balcony Right">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.5249 28.4547">
        <g id="Balcony Right">
          <path d={svgPaths.p1cabcf00} fill="var(--fill-0, white)" id="Balcony Right_2" />
        </g>
      </svg>
    </div>
  );
}

function BalconyCenter() {
  return (
    <div className="absolute h-[18.201px] left-[26.19px] top-[12.54px] w-[16.262px]" data-name="Balcony Center">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 16.2617 18.2012">
        <g id="Balcony Center">
          <path d={svgPaths.p39867380} fill="var(--fill-0, white)" id="Balcony Center_2" />
        </g>
      </svg>
    </div>
  );
}

function BalconyLeft() {
  return (
    <div className="absolute h-[28.496px] left-[43.41px] top-[5.73px] w-[21.005px]" data-name="Balcony Left">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21.0048 28.4964">
        <g id="Balcony Left">
          <path d={svgPaths.p1c956a00} fill="var(--fill-0, white)" id="Balcony Left_2" />
        </g>
      </svg>
    </div>
  );
}

function Balcony() {
  return (
    <div className="absolute contents left-[4.65px] top-[5.69px]" data-name="Balcony">
      <BalconyRight />
      <BalconyCenter />
      <BalconyLeft />
    </div>
  );
}

function LageL1() {
  return (
    <div className="absolute h-[10.442px] left-[43.46px] top-[34.69px] w-[21.005px]" data-name="Lage L">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21.0047 10.4419">
        <g id="Lage L">
          <path d={svgPaths.p2e9e7e00} fill="var(--fill-0, #E6E8EC)" id="Lage L_2" />
        </g>
      </svg>
    </div>
  );
}

function LageCenter1() {
  return (
    <div className="absolute h-[6.933px] left-[26.17px] top-[34.23px] w-[16.262px]" data-name="Lage Center">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 16.2617 6.93336">
        <g id="Lage Center">
          <path d={svgPaths.p63dbd00} fill="var(--fill-0, #E6E8EC)" id="Lage L" />
        </g>
      </svg>
    </div>
  );
}

function LageR1() {
  return (
    <div className="absolute h-[10.403px] left-[4.65px] top-[34.65px] w-[20.525px]" data-name="Lage R">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.5248 10.4027">
        <g id="Lage R">
          <path d={svgPaths.pae7f900} fill="var(--fill-0, #E6E8EC)" id="Lage L" />
        </g>
      </svg>
    </div>
  );
}

function Lage1() {
  return (
    <div className="absolute contents left-[4.65px] top-[34.23px]" data-name="Lage">
      <LageL1 />
      <LageCenter1 />
      <LageR1 />
    </div>
  );
}

function OrchLeft1() {
  return (
    <div className="absolute h-[69.663px] left-[42.73px] top-[47.46px] w-[21.731px]" data-name="Orch Left">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21.7311 69.6626">
        <g id="Orch Left">
          <path d={svgPaths.p3e769300} fill="var(--fill-0, #E6E8EC)" id="BG" />
        </g>
      </svg>
    </div>
  );
}

function OrchCenter1() {
  return (
    <div className="absolute h-[57.767px] left-[21.84px] top-[54.99px] w-[25.324px]" data-name="Orch Center">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 25.3288 57.7671">
        <g id="Orch Center">
          <path d={svgPaths.pba1ff00} fill="var(--fill-0, #E6E8EC)" id="BG" />
        </g>
      </svg>
    </div>
  );
}

function Group() {
  return (
    <div className="absolute inset-[1%_10.67%_0.99%_10.67%]" data-name="Group">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.385769 0.480676">
        <g id="Group">
          <path d={svgPaths.p25f35d00} fill="var(--fill-0, #141416)" id="Vector" />
        </g>
      </svg>
    </div>
  );
}

function DisabledIconSvg() {
  return (
    <div className="absolute inset-[21.88%] overflow-clip" data-name="disabled-icon-svg 1">
      <Group />
    </div>
  );
}

function LinkedPathGroup39() {
  return (
    <div className="-translate-x-1/2 absolute contents left-[calc(50%-3.19px)] top-[102.12px]" data-name="Linked Path Group">
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-16.16px)] size-[1.007px] top-[102.35px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-14.81px)] size-[0.998px] top-[102.12px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-6.87px)] size-[0.987px] top-[109.62px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-5.52px)] size-[0.975px] top-[109.48px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "38" } as React.CSSProperties}>
        <div className="flex-none rotate-[172.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #FFD166)" id="Rectangle 352" />
            </svg>
            <DisabledIconSvg />
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-4.15px)] size-[0.96px] top-[109.3px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p25bb8a80} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-2.79px)] size-[0.941px] top-[109.2px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-1.42px)] size-[0.914px] top-[109.12px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute left-[calc(50%-0.02px)] opacity-0 size-[0.872px] top-[109.11px]" data-name="[Copy] Seat">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
          <path d={svgPaths.p268ff600} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
        </svg>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+1.34px)] size-[0.914px] top-[109.13px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+2.7px)] size-[0.941px] top-[109.2px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+4.08px)] size-[0.96px] top-[109.31px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #E6E8EC)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+5.43px)] size-[0.975px] top-[109.47px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.25deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+6.78px)] size-[0.987px] top-[109.65px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+8.14px)] size-[0.998px] top-[109.86px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+9.79px)] size-[1.007px] top-[110.43px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup40() {
  return (
    <div className="-translate-x-1/2 absolute contents left-[calc(50%+0.08px)] top-[107.31px]" data-name="Linked Path Group">
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-9.58px)] size-[1.007px] top-[108.27px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-8.23px)] size-[0.998px] top-[108.06px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-6.88px)] size-[0.987px] top-[107.83px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-5.52px)] size-[0.975px] top-[107.66px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-7.28deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-4.16px)] size-[0.96px] top-[107.51px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p25bb8a80} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-2.8px)] size-[0.941px] top-[107.39px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-1.45px)] size-[0.914px] top-[107.32px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute left-[calc(50%-0.03px)] opacity-0 size-[0.872px] top-[107.31px]" data-name="[Copy] Seat">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
          <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
        </svg>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+1.33px)] size-[0.914px] top-[107.32px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+2.7px)] size-[0.941px] top-[107.42px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+4.06px)] size-[0.96px] top-[107.53px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+5.41px)] size-[0.975px] top-[107.67px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.25deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+6.78px)] size-[0.987px] top-[107.84px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+8.12px)] size-[0.998px] top-[108.07px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+9.74px)] size-[1.007px] top-[108.59px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup41() {
  return (
    <div className="-translate-x-1/2 absolute contents left-[calc(50%+0.08px)] top-[105.34px]" data-name="Linked Path Group">
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-9.58px)] size-[1.007px] top-[106.29px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-8.23px)] size-[0.998px] top-[106.08px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-6.88px)] size-[0.987px] top-[105.86px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-5.52px)] size-[0.975px] top-[105.7px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-7.28deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-4.16px)] size-[0.96px] top-[105.54px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p25bb8a80} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-2.8px)] size-[0.941px] top-[105.42px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-1.45px)] size-[0.914px] top-[105.35px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute left-[calc(50%-0.03px)] opacity-0 size-[0.872px] top-[105.33px]" data-name="[Copy] Seat">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
          <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
        </svg>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+1.33px)] size-[0.914px] top-[105.35px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+2.69px)] size-[0.941px] top-[105.44px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+4.06px)] size-[0.96px] top-[105.55px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+5.41px)] size-[0.975px] top-[105.69px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.25deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+6.78px)] size-[0.987px] top-[105.86px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+8.12px)] size-[0.998px] top-[106.07px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+9.74px)] size-[1.007px] top-[106.63px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup42() {
  return (
    <div className="-translate-x-1/2 absolute contents left-[calc(50%+0.08px)] top-[103.3px]" data-name="Linked Path Group">
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-9.58px)] size-[1.007px] top-[104.26px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-8.23px)] size-[0.998px] top-[104.07px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-6.88px)] size-[0.987px] top-[103.84px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-5.52px)] size-[0.975px] top-[103.67px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-7.28deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-4.16px)] size-[0.96px] top-[103.52px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p25bb8a80} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-2.8px)] size-[0.941px] top-[103.4px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-1.45px)] size-[0.914px] top-[103.32px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute left-[calc(50%-0.03px)] opacity-0 size-[0.872px] top-[103.3px]" data-name="[Copy] Seat">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
          <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
        </svg>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+1.33px)] size-[0.914px] top-[103.33px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+2.69px)] size-[0.941px] top-[103.39px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+4.06px)] size-[0.96px] top-[103.53px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+5.41px)] size-[0.975px] top-[103.67px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.25deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+6.78px)] size-[0.987px] top-[103.85px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+8.12px)] size-[0.998px] top-[104.05px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+9.74px)] size-[1.007px] top-[104.61px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedPathGroup43() {
  return (
    <div className="-translate-x-1/2 absolute contents left-[calc(50%+0.09px)] top-[101.37px]" data-name="Linked Path Group">
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-9.57px)] size-[1.007px] top-[102.31px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-8.22px)] size-[0.998px] top-[102.11px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-6.87px)] size-[0.987px] top-[101.9px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-5.51px)] size-[0.975px] top-[101.73px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-7.28deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-4.15px)] size-[0.96px] top-[101.57px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p25bb8a80} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-2.79px)] size-[0.941px] top-[101.45px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p22344780} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%-1.43px)] size-[0.914px] top-[101.38px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[-2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute left-[calc(50%-0.02px)] opacity-0 size-[0.872px] top-[101.37px]" data-name="[Copy] Seat">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
          <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
        </svg>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+1.34px)] size-[0.914px] top-[101.38px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[2.83deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+2.7px)] size-[0.941px] top-[101.47px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[4.72deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+4.07px)] size-[0.96px] top-[101.59px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[6.13deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+5.42px)] size-[0.975px] top-[101.73px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[7.25deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871887 0.871887">
              <path d={svgPaths.p217f5a00} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+6.79px)] size-[0.987px] top-[101.89px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[8.18deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+8.14px)] size-[0.998px] top-[102.13px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.01deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
      <div className="-translate-x-1/2 absolute flex items-center justify-center left-[calc(50%+9.75px)] size-[1.007px] top-[102.66px]" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
        <div className="flex-none rotate-[9.74deg]">
          <div className="opacity-0 relative size-[0.872px]" data-name="[Copy] Seat">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.871886 0.871886">
              <path d={svgPaths.p268ff600} fill="var(--fill-0, #3E8BF7)" id="Rectangle 352" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function OrchRight1() {
  return (
    <div className="absolute h-[69.945px] left-[4.66px] top-[47.51px] w-[21.731px]" data-name="Orch Right">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21.731 69.9449">
        <g id="Orch Right">
          <path d={svgPaths.p3502c00} fill="var(--fill-0, #E6E8EC)" id="BG" />
        </g>
      </svg>
    </div>
  );
}

function Orchestra1() {
  return (
    <div className="absolute contents left-[4.66px] top-[47.46px]" data-name="Orchestra">
      <OrchLeft1 />
      <OrchCenter1 />
      <LinkedPathGroup39 />
      <LinkedPathGroup40 />
      <LinkedPathGroup41 />
      <LinkedPathGroup42 />
      <LinkedPathGroup43 />
      <OrchRight1 />
    </div>
  );
}

function BalconyRight1() {
  return (
    <div className="absolute h-[28.455px] left-[4.71px] top-[5.8px] w-[20.525px]" data-name="Balcony Right">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.5249 28.4547">
        <g id="Balcony Right">
          <path d={svgPaths.pa9f7f80} fill="var(--fill-0, #E6E8EC)" id="Balcony Right_2" />
        </g>
      </svg>
    </div>
  );
}

function BalconyCenter1() {
  return (
    <div className="absolute h-[18.201px] left-[26.22px] top-[12.65px] w-[16.262px]" data-name="Balcony Center">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 16.2617 18.2012">
        <g id="Balcony Center">
          <path d={svgPaths.p37206200} fill="var(--fill-0, #E6E8EC)" id="Balcony Center_2" />
        </g>
      </svg>
    </div>
  );
}

function BalconyLeft1() {
  return (
    <div className="absolute h-[28.496px] left-[43.44px] top-[5.84px] w-[21.005px]" data-name="Balcony Left">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 21.0048 28.4964">
        <g id="Balcony Left">
          <path d={svgPaths.p3d126a00} fill="var(--fill-0, #E6E8EC)" id="Balcony Left_2" />
        </g>
      </svg>
    </div>
  );
}

function Balcony1() {
  return (
    <div className="absolute contents left-[4.71px] top-[5.8px]" data-name="Balcony">
      <BalconyRight1 />
      <BalconyCenter1 />
      <BalconyLeft1 />
    </div>
  );
}

function MapOverlay() {
  return (
    <div className="absolute contents left-[4.65px] top-[5.8px]" data-name="Map overlay">
      <Lage1 />
      <Orchestra1 />
      <Balcony1 />
    </div>
  );
}

function Map() {
  return (
    <div className="h-[137.995px] overflow-clip relative w-[69.113px]" data-name="Map 4">
      <div className="absolute flex h-[137.712px] items-center justify-center left-[0.03px] top-[0.22px] w-[69.085px]">
        <div className="flex-none rotate-180">
          <div className="h-[137.712px] relative w-[69.085px]" data-name="Frame">
            <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 69.0848 137.712">
              <path d={svgPaths.p11462272} fill="var(--fill-0, white)" id="Frame" stroke="var(--stroke-0, #E5E6EE)" strokeWidth="0.903419" />
            </svg>
          </div>
        </div>
      </div>
      <Lage />
      <Orchestra />
      <Scene />
      <Balcony />
      <MapOverlay />
    </div>
  );
}

function Frame75() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col items-center justify-end min-h-px min-w-px relative w-full">
      <div className="bg-[#3ea9f7] content-stretch flex items-center justify-center px-[16px] py-[12px] relative rounded-[90px] shrink-0" data-name="button">
        <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[16px] relative shrink-0 text-[14px] text-center text-white whitespace-nowrap" style={{ fontVariationSettings: "'opsz' 14" }}>
          Open Seat Map
        </p>
      </div>
    </div>
  );
}

function Frame70() {
  return (
    <div className="content-stretch flex flex-col gap-[32px] items-center relative rounded-[12px] self-stretch shrink-0">
      <Frame68 />
      <div className="flex items-center justify-center relative shrink-0">
        <div className="flex-none rotate-180">
          <Map />
        </div>
      </div>
      <Frame75 />
    </div>
  );
}

function Caption() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[4px] h-full items-center min-h-px min-w-px relative" data-name="Caption">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#23262f] text-[14px] whitespace-nowrap">Sales revenue</p>
      <div className="overflow-clip relative shrink-0 size-[16px]" data-name="UI icon/info/filled">
        <div className="absolute inset-[8.33%]" data-name="Subtract">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.3333 13.3333">
            <path clipRule="evenodd" d={svgPaths.pac03e80} fill="var(--fill-0, #23262F)" fillRule="evenodd" id="Subtract" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Frame5() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[40px] items-start min-h-px min-w-px relative w-full">
      <Caption />
    </div>
  );
}

function Info1() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[4px] h-[64px] items-start min-h-px min-w-px relative" data-name="Info">
      <Frame5 />
      <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[40px] relative shrink-0 text-[#23262f] text-[32px] tracking-[-0.32px] w-full" style={{ fontVariationSettings: "'opsz' 14" }}>
        $63,349.82
      </p>
    </div>
  );
}

function InfoAndSmallChart() {
  return (
    <div className="content-stretch flex flex-[1_0_0] items-start min-h-px min-w-px relative self-stretch" data-name="Info and small chart">
      <Info1 />
    </div>
  );
}

function Info() {
  return (
    <div className="content-stretch flex h-[64px] items-start relative shrink-0 w-[244px]" data-name="info">
      <InfoAndSmallChart />
    </div>
  );
}

function Frame31() {
  return (
    <div className="content-stretch flex flex-[1_0_0] items-start min-h-px min-w-px relative">
      <Info />
    </div>
  );
}

function Frame86() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col items-end min-h-px min-w-px not-italic relative whitespace-nowrap">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] relative shrink-0 text-[#353945] text-[14px]">Potential revenue</p>
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] relative shrink-0 text-[#777e90] text-[14px]">
        <p className="leading-[1.7]">4 Price levels</p>
      </div>
      <p className="font-['Poppins:SemiBold',sans-serif] leading-[24px] relative shrink-0 text-[#353945] text-[16px]">$138,835.96</p>
    </div>
  );
}

function Frame27() {
  return (
    <div className="content-stretch flex gap-[10px] items-start relative shrink-0 w-full">
      <Frame31 />
      <Frame86 />
    </div>
  );
}

function Frame16() {
  return <div className="bg-[#f4f5f6] col-1 h-[14px] ml-0 mt-0 rounded-[18px] row-1 w-full" />;
}

function Frame17() {
  return <div className="bg-[#3ea9f7] col-1 h-[14px] ml-0 mt-0 rounded-[28px] row-1 w-[7.099999999999994%]" />;
}

function Group1() {
  return (
    <div className="grid-rows-[max-content] inline-grid leading-[0] place-items-start relative shrink-0 w-full">
      <Frame16 />
      <Frame17 />
    </div>
  );
}

function Frame23() {
  return (
    <div className="content-stretch flex flex-col h-[14px] items-start relative shrink-0 w-full">
      <Group1 />
    </div>
  );
}

function Frame80() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0 w-full">
      <Frame27 />
      <Frame23 />
    </div>
  );
}

function Frame51() {
  return (
    <div className="content-stretch flex gap-[8px] items-center relative shrink-0">
      <div className="bg-[#ffd166] rounded-[8px] shrink-0 size-[16px]" />
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">Open</p>
      </div>
    </div>
  );
}

function Frame52() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">780</p>
      </div>
    </div>
  );
}

function Frame50() {
  return (
    <div className="content-stretch flex items-start justify-between relative shrink-0 w-full">
      <Frame51 />
      <Frame52 />
    </div>
  );
}

function Col() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start justify-center relative shrink-0 w-full" data-name="Col">
      <Frame50 />
    </div>
  );
}

function Frame54() {
  return (
    <div className="content-stretch flex gap-[8px] items-center relative shrink-0">
      <div className="bg-[#9757d7] rounded-[8px] shrink-0 size-[16px]" />
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">Restricted</p>
      </div>
    </div>
  );
}

function Frame55() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">120</p>
      </div>
    </div>
  );
}

function Frame53() {
  return (
    <div className="content-stretch flex items-start justify-between relative shrink-0 w-full">
      <Frame54 />
      <Frame55 />
    </div>
  );
}

function Col1() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start justify-center relative shrink-0 w-full" data-name="Col">
      <Frame53 />
    </div>
  );
}

function Frame57() {
  return (
    <div className="content-stretch flex gap-[8px] items-center relative shrink-0">
      <div className="bg-[#ef466f] rounded-[8px] shrink-0 size-[16px]" />
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">Hold</p>
      </div>
    </div>
  );
}

function Frame58() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">80</p>
      </div>
    </div>
  );
}

function Frame56() {
  return (
    <div className="content-stretch flex items-start justify-between relative shrink-0 w-full">
      <Frame57 />
      <Frame58 />
    </div>
  );
}

function Col2() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start justify-center relative shrink-0 w-full" data-name="Col">
      <Frame56 />
    </div>
  );
}

function Frame61() {
  return (
    <div className="content-stretch flex gap-[8px] items-center relative shrink-0">
      <div className="bg-[#b1b5c3] rounded-[8px] shrink-0 size-[16px]" />
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">Kill</p>
      </div>
    </div>
  );
}

function Frame62() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">16</p>
      </div>
    </div>
  );
}

function Frame60() {
  return (
    <div className="content-stretch flex items-start justify-between relative shrink-0 w-full">
      <Frame61 />
      <Frame62 />
    </div>
  );
}

function Col3() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start justify-center relative shrink-0 w-full" data-name="Col">
      <Frame60 />
    </div>
  );
}

function Frame64() {
  return (
    <div className="content-stretch flex gap-[8px] items-center relative shrink-0">
      <div className="bg-[#3ea9f7] rounded-[8px] shrink-0 size-[16px]" />
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">Sold</p>
      </div>
    </div>
  );
}

function Frame65() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#353945] text-[14px] whitespace-nowrap">
        <p className="leading-[1.7]">94</p>
      </div>
    </div>
  );
}

function Frame63() {
  return (
    <div className="content-stretch flex items-start justify-between relative shrink-0 w-full">
      <Frame64 />
      <Frame65 />
    </div>
  );
}

function Col4() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start justify-center relative shrink-0 w-full" data-name="Col">
      <Frame63 />
    </div>
  );
}

function Frame71() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[8px] items-start min-h-px min-w-px relative">
      <Col />
      <Col1 />
      <Col2 />
      <Col3 />
      <Col4 />
    </div>
  );
}

function Seats() {
  return (
    <div className="col-1 content-stretch flex flex-col items-center justify-center ml-[36px] mt-[42px] not-italic pb-[4px] relative row-1 text-center whitespace-nowrap" data-name="seats">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center mb-[-4px] relative shrink-0 text-[#777e90] text-[12px]">
        <p className="leading-[20px]">Capacity</p>
      </div>
      <div className="flex flex-col font-['Poppins:SemiBold',sans-serif] justify-center mb-[-4px] relative shrink-0 text-[#141416] text-[24px]">
        <p className="leading-[32px]">10,580</p>
      </div>
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center mb-[-4px] relative shrink-0 text-[#777e90] text-[12px]">
        <p className="leading-[20px]">Seats</p>
      </div>
    </div>
  );
}

function Group2() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] place-items-start relative shrink-0">
      <Seats />
      <div className="col-1 h-[148px] ml-[0.39px] mt-0 relative row-1 w-[149px]">
        <div className="absolute inset-[0_40.92%_87.18%_31.57%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 40.9963 18.9704">
            <path d={svgPaths.p1ff7a800} fill="var(--fill-0, #B1B5C4)" id="Ellipse 236" />
          </svg>
        </div>
      </div>
      <div className="col-1 h-[148px] ml-[0.39px] mt-0 relative row-1 w-[149px]">
        <div className="absolute inset-[0.96%_57.8%_78.28%_14.64%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 41.0631 30.7201">
            <path d={svgPaths.p34657800} fill="var(--fill-0, #EF466F)" id="Ellipse 237" />
          </svg>
        </div>
      </div>
      <div className="col-1 h-[148px] ml-[0.39px] mt-0 relative row-1 w-[149px]">
        <div className="absolute inset-[7.72%_71.36%_55%_0.39%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 42.0954 55.1711">
            <path d={svgPaths.p4afa340} fill="var(--fill-0, #9757D7)" id="Ellipse 234" />
          </svg>
        </div>
      </div>
      <div className="col-1 h-[148px] ml-[0.39px] mt-0 relative row-1 w-[149px]">
        <div className="absolute inset-[28.33%_86.05%_41.55%_0]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.7877 44.5721">
            <path d={svgPaths.p37fbcf00} fill="var(--fill-0, #3EA9F7)" id="Ellipse 238" />
          </svg>
        </div>
      </div>
      <div className="col-1 h-[148px] ml-0 mt-0 relative row-1 w-[149px]">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 149 148">
          <path d={svgPaths.p34e05f00} fill="var(--fill-0, #FFD166)" id="Ellipse 235" />
        </svg>
      </div>
    </div>
  );
}

function Frame87() {
  return (
    <div className="content-stretch flex gap-[40px] items-start relative shrink-0 w-full">
      <Frame71 />
      <Group2 />
    </div>
  );
}

function Frame59() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[16px] items-start min-h-px min-w-px relative">
      <div className="flex flex-col font-['Poppins:Bold',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#141416] text-[12px] uppercase whitespace-nowrap">
        <p className="leading-[12px]">Inventory</p>
      </div>
      <Frame87 />
    </div>
  );
}

function Frame72() {
  return (
    <div className="content-stretch flex items-center relative shrink-0 w-full">
      <Frame59 />
    </div>
  );
}

function Frame22() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[40px] items-start min-h-px min-w-px relative">
      <Frame80 />
      <Frame72 />
    </div>
  );
}

function Frame20() {
  return (
    <div className="bg-white relative rounded-[12px] shrink-0 w-full">
      <div className="content-stretch flex gap-[32px] items-start p-[32px] relative w-full">
        <Frame70 />
        <div className="flex h-0 items-center justify-center relative self-center shrink-0 w-0" style={{ "--transform-inner-width": "1200", "--transform-inner-height": "19" } as React.CSSProperties}>
          <div className="flex-none h-full rotate-90">
            <div className="h-full relative w-[314px]">
              <div className="absolute inset-[-1px_0_0_0]">
                <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 314 1">
                  <line id="Line 9" stroke="var(--stroke-0, #E6E8EC)" x2="314" y1="0.5" y2="0.5" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        <Frame22 />
      </div>
    </div>
  );
}

function Icon48PlaceHolder() {
  return (
    <div className="bg-[#f4f5f6] overflow-clip relative rounded-[48px] shrink-0 size-[48px]" data-name="Icon/48 place holder">
      <div className="absolute left-[12px] overflow-clip size-[24px] top-[12px]" data-name="Icons/UI icon/dollar/light">
        <div className="absolute inset-[4.17%_20.83%]" data-name="Union">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 22">
            <path d={svgPaths.p1f179580} fill="var(--fill-0, #777E91)" id="Union" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Frame32() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <Icon48PlaceHolder />
    </div>
  );
}

function Caption1() {
  return (
    <div className="content-stretch flex gap-[4px] h-full items-center relative shrink-0" data-name="Caption">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#23262f] text-[14px] whitespace-nowrap">{`Royalties `}</p>
      <div className="overflow-clip relative shrink-0 size-[16px]" data-name="UI icon/info/filled">
        <div className="absolute inset-[8.33%]" data-name="Subtract">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.3333 13.3333">
            <path clipRule="evenodd" d={svgPaths.pac03e80} fill="var(--fill-0, #23262F)" fillRule="evenodd" id="Subtract" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Frame6() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[40px] items-start min-h-px min-w-px relative w-full">
      <Caption1 />
    </div>
  );
}

function Info2() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[4px] h-[64px] items-start min-h-px min-w-px relative" data-name="Info">
      <Frame6 />
      <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[40px] relative shrink-0 text-[#23262f] text-[32px] tracking-[-0.32px] w-full" style={{ fontVariationSettings: "'opsz' 14" }}>
        $52.532.23
      </p>
    </div>
  );
}

function Frame28() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-full">
      <Frame32 />
      <Info2 />
    </div>
  );
}

function Frame24() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0 w-full">
      <Frame28 />
    </div>
  );
}

function Frame29() {
  return (
    <div className="content-stretch flex items-center relative shrink-0 w-full">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#141416] text-[0px] tracking-[-0.24px] whitespace-nowrap">
        <p>
          <span className="font-['Poppins:SemiBold',sans-serif] leading-[24px] not-italic text-[16px]">10,000</span>
          <span className="leading-[32px] text-[24px]">{` `}</span>
          <span className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic text-[#777e90] text-[14px]">Tickets Sold</span>
        </p>
      </div>
    </div>
  );
}

function Frame21() {
  return (
    <div className="bg-white flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]">
      <div className="content-stretch flex flex-col gap-[14px] items-start px-[32px] py-[24px] relative w-full">
        <Frame24 />
        <Frame29 />
      </div>
    </div>
  );
}

function Eye() {
  return (
    <div className="absolute inset-[8.33%]" data-name="eye">
      <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
        <g clipPath="url(#clip0_1_3499)" id="eye">
          <path d={svgPaths.p3d74ed00} id="Vector" stroke="var(--stroke-0, #777E91)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
          <path d={svgPaths.p3b27f100} id="Vector_2" stroke="var(--stroke-0, #777E91)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
        </g>
        <defs>
          <clipPath id="clip0_1_3499">
            <rect fill="white" height="20" width="20" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}

function Icon48PlaceHolder1() {
  return (
    <div className="bg-[#f4f5f6] overflow-clip relative rounded-[48px] shrink-0 size-[48px]" data-name="Icon/48 place holder">
      <div className="absolute left-[12px] overflow-clip size-[24px] top-[12px]" data-name="Icons/icons/Eye/Line">
        <Eye />
      </div>
    </div>
  );
}

function Frame33() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <Icon48PlaceHolder1 />
    </div>
  );
}

function Caption2() {
  return (
    <div className="content-stretch flex gap-[4px] h-full items-center relative shrink-0" data-name="Caption">
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic relative shrink-0 text-[#23262f] text-[14px] whitespace-nowrap">Page views</p>
      <div className="overflow-clip relative shrink-0 size-[16px]" data-name="UI icon/info/filled">
        <div className="absolute inset-[8.33%]" data-name="Subtract">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.3333 13.3333">
            <path clipRule="evenodd" d={svgPaths.pac03e80} fill="var(--fill-0, #23262F)" fillRule="evenodd" id="Subtract" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Frame7() {
  return (
    <div className="content-stretch flex flex-[1_0_0] gap-[40px] items-start min-h-px min-w-px relative w-full">
      <Caption2 />
    </div>
  );
}

function Info3() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[4px] h-[64px] items-start min-h-px min-w-px relative" data-name="Info">
      <Frame7 />
      <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[40px] relative shrink-0 text-[#23262f] text-[32px] tracking-[-0.32px] w-full" style={{ fontVariationSettings: "'opsz' 14" }}>
        42,495
      </p>
    </div>
  );
}

function Frame30() {
  return (
    <div className="content-stretch flex gap-[16px] items-center relative shrink-0 w-full">
      <Frame33 />
      <Info3 />
    </div>
  );
}

function Frame26() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0 w-full">
      <Frame30 />
    </div>
  );
}

function Frame34() {
  return (
    <div className="content-stretch flex items-center relative shrink-0 w-full">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#141416] text-[0px] tracking-[-0.24px] whitespace-nowrap">
        <p>
          <span className="font-['Poppins:SemiBold',sans-serif] leading-[24px] not-italic text-[16px]">12%</span>
          <span className="leading-[32px] text-[24px]">{` `}</span>
          <span className="font-['Poppins:Medium',sans-serif] leading-[24px] not-italic text-[#777e90] text-[14px]">Avg. Conversion</span>
        </p>
      </div>
    </div>
  );
}

function Frame25() {
  return (
    <div className="bg-white flex-[1_0_0] min-h-px min-w-px relative rounded-[12px] w-full">
      <div className="content-stretch flex flex-col gap-[14px] items-start px-[32px] py-[24px] relative size-full">
        <Frame26 />
        <Frame34 />
      </div>
    </div>
  );
}

function TicketsSold() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col items-start justify-center min-h-px min-w-px relative self-stretch" data-name="Tickets sold">
      <Frame25 />
    </div>
  );
}

function Frame84() {
  return (
    <div className="content-stretch flex gap-[32px] items-start relative shrink-0 w-full">
      <Frame21 />
      <TicketsSold />
    </div>
  );
}

function Frame76() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start not-italic relative shrink-0 text-black whitespace-nowrap">
      <p className="font-['Poppins:Bold',sans-serif] leading-[16px] relative shrink-0 text-[16px] uppercase">Offers</p>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] relative shrink-0 text-[14px]">You have 3 offers</p>
    </div>
  );
}

function Frame35() {
  return (
    <div className="bg-white flex-[1_0_0] min-h-px min-w-px relative rounded-[12px]">
      <div className="content-stretch flex flex-col gap-[14px] items-start px-[32px] py-[24px] relative w-full">
        <Frame76 />
        <div className="bg-[#3ea9f7] relative rounded-[90px] shrink-0 w-full" data-name="button">
          <div className="flex flex-row items-center justify-center size-full">
            <div className="content-stretch flex items-center justify-center px-[16px] py-[12px] relative w-full">
              <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[16px] relative shrink-0 text-[14px] text-center text-white whitespace-nowrap" style={{ fontVariationSettings: "'opsz' 14" }}>
                Manage offers
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Frame77() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start not-italic relative shrink-0 text-black whitespace-nowrap">
      <p className="font-['Poppins:Bold',sans-serif] leading-[16px] relative shrink-0 text-[16px] uppercase">qr-code</p>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] relative shrink-0 text-[14px]">Share your event</p>
    </div>
  );
}

function Frame36() {
  return (
    <div className="bg-white flex-[1_0_0] min-h-px min-w-px relative rounded-[12px] self-stretch">
      <div className="content-stretch flex flex-col items-start justify-between px-[32px] py-[24px] relative size-full">
        <Frame77 />
        <div className="relative rounded-[90px] shrink-0 w-full" data-name="button">
          <div aria-hidden="true" className="absolute border-2 border-[#e6e8ec] border-solid inset-0 pointer-events-none rounded-[90px]" />
          <div className="flex flex-row items-center justify-center size-full">
            <div className="content-stretch flex items-center justify-center px-[16px] py-[12px] relative w-full">
              <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[16px] relative shrink-0 text-[#23262f] text-[14px] text-center whitespace-nowrap" style={{ fontVariationSettings: "'opsz' 14" }}>
                Download PNG
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Frame85() {
  return (
    <div className="content-stretch flex gap-[32px] items-start relative shrink-0 w-full">
      <Frame35 />
      <Frame36 />
    </div>
  );
}

function Frame78() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start not-italic relative shrink-0 text-black whitespace-nowrap">
      <p className="font-['Poppins:Bold',sans-serif] leading-[16px] relative shrink-0 text-[16px] uppercase">Event listing</p>
      <p className="font-['Poppins:Medium',sans-serif] leading-[24px] relative shrink-0 text-[14px]">Your event listing is now available</p>
    </div>
  );
}

function Frame79() {
  return (
    <div className="content-stretch flex gap-[14px] items-start relative shrink-0">
      <div className="content-stretch flex items-center justify-center px-[16px] py-[12px] relative rounded-[90px] shrink-0" data-name="button">
        <div aria-hidden="true" className="absolute border-2 border-[#e6e8ec] border-solid inset-0 pointer-events-none rounded-[90px]" />
        <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[16px] relative shrink-0 text-[#23262f] text-[14px] text-center whitespace-nowrap" style={{ fontVariationSettings: "'opsz' 14" }}>
          Copy link
        </p>
      </div>
      <div className="bg-[#3ea9f7] content-stretch flex items-center justify-center px-[16px] py-[12px] relative rounded-[90px] shrink-0" data-name="button">
        <p className="font-['DM_Sans:Bold',sans-serif] font-bold leading-[16px] relative shrink-0 text-[14px] text-center text-white whitespace-nowrap" style={{ fontVariationSettings: "'opsz' 14" }}>
          Open event page
        </p>
      </div>
    </div>
  );
}

function Frame37() {
  return (
    <div className="bg-white relative rounded-[12px] shrink-0 w-full">
      <div className="flex flex-row items-center size-full">
        <div className="content-stretch flex items-center justify-between px-[32px] py-[24px] relative w-full">
          <Frame78 />
          <Frame79 />
        </div>
      </div>
    </div>
  );
}

function Frame82() {
  return (
    <div className="content-stretch flex flex-col gap-[32px] items-start relative shrink-0 w-[705px]">
      <Frame20 />
      <Frame84 />
      <Frame85 />
      <Frame37 />
    </div>
  );
}

function Frame1() {
  return (
    <div className="h-[277px] overflow-clip relative rounded-[11.396px] shrink-0 w-[277.003px]">
      <div className="absolute h-[278.246px] left-[0.02px] top-[-0.01px] w-[276.354px]" data-name="slide 01 - light 1">
        <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgSlide01Light1} />
      </div>
    </div>
  );
}

function Frame74() {
  return (
    <div className="content-stretch flex isolate items-start pointer-events-none pr-[12px] relative shrink-0">
      <div className="mr-[-12px] relative rounded-[30.003px] shrink-0 size-[40px] z-[2]" data-name="slide 01 - light 1">
        <img alt="" className="absolute inset-0 max-w-none object-cover rounded-[30.003px] size-full" src={imgSlide01Light1} />
        <div aria-hidden="true" className="absolute border border-solid border-white inset-0 rounded-[30.003px]" />
      </div>
      <div className="mr-[-12px] relative rounded-[25.381px] shrink-0 size-[40px] z-[1]" data-name="slide 01 - light 2">
        <img alt="" className="absolute inset-0 max-w-none object-cover rounded-[25.381px] size-full" src={imgSlide01Light1} />
        <div aria-hidden="true" className="absolute border-[0.846px] border-solid border-white inset-0 rounded-[25.381px]" />
      </div>
    </div>
  );
}

function Frame73() {
  return (
    <div className="content-stretch flex items-center justify-between relative shrink-0 w-full">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[14px] text-black text-center whitespace-nowrap">
        <p className="leading-[1.7]">Attractions</p>
      </div>
      <Frame74 />
    </div>
  );
}

function Frame67() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start not-italic relative shrink-0 text-[#141416] whitespace-nowrap">
      <p className="font-['Poppins:Bold',sans-serif] leading-[16px] relative shrink-0 text-[16px] uppercase">General onsale</p>
      <p className="font-['Poppins:Regular',sans-serif] leading-[1.7] relative shrink-0 text-[14px]">Thu • Mar 13 • 9:00 PM EST</p>
    </div>
  );
}

function Frame46() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0 w-full">
      <Frame67 />
    </div>
  );
}

function Frame45() {
  return (
    <div className="content-stretch flex flex-col gap-[16px] items-center relative shrink-0 w-full">
      <Frame1 />
      <Frame73 />
      <Frame46 />
    </div>
  );
}

function Frame81() {
  return (
    <div className="content-stretch flex items-center relative shrink-0 w-full">
      <div className="flex flex-col font-['Poppins:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[14px] text-black text-center whitespace-nowrap">
        <p className="leading-[1.7]">+1 other sales period</p>
      </div>
    </div>
  );
}

function Frame38() {
  return (
    <div className="bg-white relative rounded-[12px] shrink-0 w-full">
      <div className="content-stretch flex flex-col gap-[8px] items-start p-[24px] relative w-full">
        <Frame45 />
        <Frame81 />
      </div>
    </div>
  );
}

function Icon48PlaceHolder2() {
  return (
    <div className="bg-[#f4f5f6] overflow-clip relative rounded-[48px] shrink-0 size-[48px]" data-name="Icon/48 place holder">
      <div className="absolute left-[12px] overflow-clip size-[24px] top-[12px]" data-name="Icons/UI icon/settings/light">
        <div className="absolute inset-[33.33%]" data-name="Oval (Stroke)">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 8 8">
            <path clipRule="evenodd" d={svgPaths.p20484100} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Oval (Stroke)" />
          </svg>
        </div>
        <div className="absolute inset-[4.17%_7.9%]" data-name="Union (Stroke)">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.2095 22">
            <path clipRule="evenodd" d={svgPaths.p54642b0} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Union (Stroke)" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Frame40() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <Icon48PlaceHolder2 />
    </div>
  );
}

function Frame39() {
  return (
    <div className="bg-white relative rounded-[12px] shrink-0 w-full">
      <div className="flex flex-row items-center size-full">
        <div className="content-stretch flex gap-[16px] items-center px-[24px] py-[16px] relative w-full">
          <Frame40 />
          <p className="flex-[1_0_0] font-['Poppins:Regular',sans-serif] leading-[24px] min-h-px min-w-px not-italic relative text-[16px] text-black">Event settings</p>
        </div>
      </div>
    </div>
  );
}

function Icon48PlaceHolder3() {
  return (
    <div className="bg-[#f4f5f6] overflow-clip relative rounded-[48px] shrink-0 size-[48px]" data-name="Icon/48 place holder">
      <div className="absolute left-[12px] overflow-clip size-[24px] top-[12px]" data-name="Icons/icons/Info Circle/Line">
        <div className="absolute inset-[8.33%]" data-name="Shape">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
            <path clipRule="evenodd" d={svgPaths.p3f44d800} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Shape" />
          </svg>
        </div>
        <div className="absolute inset-[29.17%_45.83%]" data-name="Shape">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 2 10">
            <path clipRule="evenodd" d={svgPaths.p3ed62400} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Shape" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Frame42() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <Icon48PlaceHolder3 />
    </div>
  );
}

function Frame41() {
  return (
    <div className="bg-white relative rounded-[12px] shrink-0 w-full">
      <div className="flex flex-row items-center size-full">
        <div className="content-stretch flex gap-[16px] items-center px-[24px] py-[16px] relative w-full">
          <Frame42 />
          <p className="font-['Poppins:Regular',sans-serif] leading-[24px] not-italic relative shrink-0 text-[16px] text-black whitespace-nowrap">Event Details</p>
        </div>
      </div>
    </div>
  );
}

function Icon48PlaceHolder4() {
  return (
    <div className="bg-[#f4f5f6] overflow-clip relative rounded-[48px] shrink-0 size-[48px]" data-name="Icon/48 place holder">
      <div className="absolute left-[12px] overflow-clip size-[24px] top-[12px]" data-name="Icons/icons/Star/Line">
        <div className="absolute inset-[8.33%]" data-name="Shape">
          <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
            <path clipRule="evenodd" d={svgPaths.p2e81b570} fill="var(--fill-0, #777E91)" fillRule="evenodd" id="Shape" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Frame44() {
  return (
    <div className="content-stretch flex items-center relative shrink-0">
      <Icon48PlaceHolder4 />
    </div>
  );
}

function Frame43() {
  return (
    <div className="bg-white relative rounded-[12px] shrink-0 w-full">
      <div className="flex flex-row items-center size-full">
        <div className="content-stretch flex gap-[16px] items-center px-[24px] py-[16px] relative w-full">
          <Frame44 />
          <p className="font-['Poppins:Regular',sans-serif] leading-[24px] not-italic relative shrink-0 text-[16px] text-black whitespace-nowrap">Add-ons</p>
        </div>
      </div>
    </div>
  );
}

function Frame88() {
  return (
    <div className="content-stretch flex flex-col gap-[16px] items-start relative shrink-0 w-full">
      <Frame39 />
      <Frame41 />
      <Frame43 />
    </div>
  );
}

function TicketsSold1() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[32px] items-start min-h-px min-w-px relative" data-name="Tickets sold">
      <Frame38 />
      <Frame88 />
    </div>
  );
}

function Frame83() {
  return (
    <div className="content-stretch flex gap-[32px] items-start relative shrink-0 w-full">
      <Frame82 />
      <TicketsSold1 />
    </div>
  );
}

function Frame8() {
  return (
    <div className="content-stretch flex flex-[1_0_0] flex-col gap-[32px] items-start min-h-px min-w-px pt-[32px] relative">
      <Frame19 />
      <Frame83 />
    </div>
  );
}

function Frame66() {
  return (
    <div className="content-stretch flex gap-[32px] h-[1244px] items-start pr-[32px] relative shrink-0 w-[1440px]">
      <div className="bg-white h-full relative shrink-0 w-[314px]" data-name="Side menu">
        <div className="overflow-clip rounded-[inherit] size-full">
          <div className="content-stretch flex flex-col items-start justify-between px-[32px] py-[24px] relative size-full">
            <TopElements />
            <Bottom />
          </div>
        </div>
        <div aria-hidden="true" className="absolute border-[#e6e8ec] border-r border-solid border-t inset-0 pointer-events-none" />
      </div>
      <Frame8 />
    </div>
  );
}

export default function Seatmap() {
  return (
    <div className="bg-[#f4f5f6] content-stretch flex flex-col items-start relative size-full" data-name="seatmap">
      <div className="bg-white content-stretch flex flex-col items-start relative shrink-0" data-name="Nav">
        <NavContent />
        <Dropdown />
      </div>
      <div className="bg-white content-stretch flex flex-col h-[64px] items-start relative shrink-0 w-[1440px]" data-name="Event Bar/Event Info Bar Mobile S">
        <div aria-hidden="true" className="absolute border-[#e6e8ec] border-solid border-t-8 inset-0 pointer-events-none" />
        <NavDesktopLightLoggedDropdown />
        <Divider />
      </div>
      <Frame66 />
    </div>
  );
}