import { X } from "lucide-react";
import { motion } from "motion/react";
import type { ReactNode } from "react";
import { spring } from "../../motion/tokens";
import styles from "./Sheet.module.css";
export function Sheet({title,close,children,className=""}:{title:string;close:()=>void;children:ReactNode;className?:string}){return <motion.div className={styles.backdrop} initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} onClick={close}><motion.section className={`${styles.sheet} ${className}`} initial={{y:30,opacity:0}} animate={{y:0,opacity:1}} exit={{y:20,opacity:0}} transition={spring.panel} onClick={e=>e.stopPropagation()}><header><h2>{title}</h2><button onClick={close} aria-label="Close"><X/></button></header>{children}</motion.section></motion.div>}
