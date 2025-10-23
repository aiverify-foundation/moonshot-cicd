import { Home } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

// Menu items.
const items = [
  {
    title: "Home",
    url: "/",
    icon: Home,
    testId: "sidebar-back-to-home-button",
  },
]

export function AppSidebar() {
  return (
    <Sidebar collapsible="none" className="w-12 border-r h-screen fixed left-0 top-0 z-40">
      <SidebarContent className="h-full">
        <SidebarGroup className="h-full">
          <SidebarGroupContent className="h-full flex items-start">
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild tooltip={item.title}>
                    <a href={item.url} data-testid={item.testId}>
                      <item.icon />
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}