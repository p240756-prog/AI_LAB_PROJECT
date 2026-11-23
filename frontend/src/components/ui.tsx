import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { cva, type VariantProps } from 'class-variance-authority';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { X } from 'lucide-react';
export const cn=(...inputs:ClassValue[])=>twMerge(clsx(inputs));
// shadcn/ui composition patterns, styled with the Plant Disease Lab tokens.
const buttonVariants=cva('lab-button',{variants:{variant:{default:'lab-button-primary',secondary:'lab-button-secondary',ghost:'lab-button-ghost'},size:{default:'',small:'lab-button-small',icon:'lab-button-icon'}},defaultVariants:{variant:'default',size:'default'}});
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>,VariantProps<typeof buttonVariants>{asChild?:boolean}
export const Button=React.forwardRef<HTMLButtonElement,ButtonProps>(({className,variant,size,asChild=false,...props},ref)=>{const Comp=asChild?Slot:'button';return <Comp type="button" className={cn(buttonVariants({variant,size,className}))} ref={ref} {...props}/>;});
Button.displayName='Button';
export const Dialog=DialogPrimitive.Root;
export const DialogTrigger=DialogPrimitive.Trigger;
export const DialogClose=DialogPrimitive.Close;
export const DialogTitle=DialogPrimitive.Title;
export const DialogDescription=DialogPrimitive.Description;
export const DialogContent=React.forwardRef<React.ElementRef<typeof DialogPrimitive.Content>,React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>>(({className,children,...props},ref)=><DialogPrimitive.Portal><DialogPrimitive.Overlay className="lab-dialog-overlay"/><DialogPrimitive.Content ref={ref} className={cn('lab-dialog',className)} {...props}>{children}<DialogPrimitive.Close className="lab-dialog-close" aria-label="Close dialog"><X size={19}/></DialogPrimitive.Close></DialogPrimitive.Content></DialogPrimitive.Portal>);
DialogContent.displayName='DialogContent';
