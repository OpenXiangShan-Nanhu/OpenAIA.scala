package aia

import chisel3._
import chisel3.util._
import freechips.rocketchip.diplomacy._
import org.chipsalliance.cde.config.Parameters
import freechips.rocketchip.tilelink._
import freechips.rocketchip.regmapper._
import freechips.rocketchip.prci.{ClockSinkDomain}
import freechips.rocketchip.util._
import xs.utils._

// _root_ disambiguates from package chisel3.util.circt if user imports chisel3.util._
import _root_.circt.stage.ChiselStage

object pow2 {
  def apply(n: Int): Long = 1L << n
}

case class IntFileParams(
  membersNum      : Int  = 2           ,// h_max: members number with in a group

  mBaseAddr       : Long = 0x61000000L ,// A: base addr for machine-level interrupt files
  mStrideBits     : Int  = 12          ,// C: stride between each machine-level interrupt files

  sgBaseAddr      : Long = 0x82900000L ,// B: base addr for supervisor- and guest-level interrupt files
  sgStrideBits    : Int  = 15          ,// D: stride between each supervisor- and guest-level interrupt files
  geilen          : Int  = 4           ,// number of guest interrupt files

  groupsNum       : Int  = 1           ,// g_max: groups number
  groupStrideBits : Int  = 16          ,// E: stride between each interrupt file groups
) {
  val intFileWidth: Int  = 12           // interrupt file width: 12-bit width => 4KB size

  val k: Int = log2Ceil(membersNum)
  println(f"IntFileParams.k: ${k}%d")
  require((mBaseAddr & (pow2(k + mStrideBits) -1)) == 0, "mBaseAddr should be aligned to a 2^(k+C)")
  require(mStrideBits >= 12)

  require(sgStrideBits >= log2Ceil(geilen+1)+12)

  require(groupStrideBits >= k + math.max(mStrideBits, sgStrideBits))

  val j: Int = log2Ceil(groupsNum + 1)
  println(f"IntFileParams.j: ${j}%d")
  require((sgBaseAddr & (pow2(k + sgStrideBits) - 1)) == 0, "sgBaseAddr should be aligned to a 2^(k+D)")

  require((
    ((pow2(j)-1) * pow2(groupStrideBits))
    & mBaseAddr
  ) == 0)
  require((
    ((pow2(j)-1) * pow2(groupStrideBits))
    & sgBaseAddr
  ) == 0)

  println(f"IntFileParams.membersNum:        ${membersNum     }%d")
  println(f"IntFileParams.mBaseAddr:       0x${mBaseAddr      }%x")
  println(f"IntFileParams.mStrideBits:       ${mStrideBits    }%d")
  println(f"IntFileParams.sgBaseAddr:      0x${sgBaseAddr     }%x")
  println(f"IntFileParams.sgStrideBits:      ${sgStrideBits   }%d")
  println(f"IntFileParams.geilen:            ${geilen         }%d")
  println(f"IntFileParams.groupsNum:         ${groupsNum      }%d")
  println(f"IntFileParams.groupStrideBits:   ${groupStrideBits}%d")
}

// TODO: implement all signals in the belowing two bundles
// Based on Xiangshan NewCSR
class CSRToIMSICBundle extends Bundle {
  private final val AddrWidth = 12

  // val addr = ValidIO(new Bundle {
  //   val addr = UInt(AddrWidth.W)
  //   val virt = Bool()
  //   val priv = UInt(2.W) // U, S, M
  // })

  // val VGEINWidth = 6
  // val vgein = UInt(VGEINWidth.W)

  // val wdata = ValidIO(new Bundle {
  //   val op = UInt(2.W)
  //   val data = UInt(64.W)
  // })

  // val mClaim = Bool()
  // val sClaim = Bool()
  // val vsClaim = Bool()
}
class IMSICToCSRBundle extends Bundle {
  // private val NumVSIRFiles = 63
  // val rdata = ValidIO(new Bundle {
  //   val data = UInt(64.W)
  //   val illegal = Bool()
  // })
  val meip    = Bool()
  // val seip    = Bool()
  // val vseip   = UInt(NumVSIRFiles.W)
  // 11 bits: 32*64 = 2048 interrupt sources
  val mtopei  = UInt(11.W)
  // val stopei  = UInt(11.W)
  // val vstopei = UInt(11.W)
}


class TLIMSIC(
  intFileParams: IntFileParams,
  groupID: Int = 0, // g
  memberID: Int = 1, // h
  beatBytes: Int = 8,
)(implicit p: Parameters) extends LazyModule {
  require(groupID < intFileParams.groupsNum,    f"groupID ${groupID} should less than groupsNum ${intFileParams.groupsNum}")
  require(memberID < intFileParams.membersNum,  f"memberID ${memberID} should less than membersNum ${intFileParams.membersNum}")
  println(f"groupID:  0x${groupID }%x")
  println(f"memberID: 0x${memberID}%x")

  val device: SimpleDevice = new SimpleDevice(
    "interrupt-controller",
    Seq(f"riscv,imsic.${groupID}%d.${memberID}%d")
  ) {}


  // addr for the machine-level interrupt file: g*2^E + A + h*2^C
  val mIntFileAddr = AddressSet(
    groupID * pow2(intFileParams.groupStrideBits) + intFileParams.mBaseAddr + memberID * pow2(intFileParams.mStrideBits),
    pow2(intFileParams.intFileWidth) - 1
  )
  // addr for the supervisor-level and guest-level interrupt files: g*2^E + B + h*2^D
  val sgIntFileAddr = AddressSet(
    groupID * pow2(intFileParams.groupStrideBits) + intFileParams.sgBaseAddr + memberID * pow2(intFileParams.sgStrideBits),
    pow2(intFileParams.intFileWidth) * (1+intFileParams.geilen) - 1
  )
  println(f"mIntFileAddr:  [0x${mIntFileAddr.base }%x, 0x${mIntFileAddr.max }%x]")
  println(f"sgIntFileAddr: [0x${sgIntFileAddr.base}%x, 0x${sgIntFileAddr.max}%x]")

  val mIntFileNode: TLRegisterNode = TLRegisterNode(
    address = Seq(mIntFileAddr),
    device = device,
    beatBytes = beatBytes,
    undefZero = true,
    concurrency = 1
  )

  lazy val module = new LazyModuleImp(this) {
    val toCSR = IO(Output(new IMSICToCSRBundle))
    val fromCSR = IO(Input(new CSRToIMSICBundle))
    dontTouch(toCSR)
    dontTouch(fromCSR)

    // TODO: Add a struct for these CSRs in a interrupt file
    /// indirect CSRs
    val meidelivery = RegInit(1.U(64.W)) // TODO: default: disable it
    val meithreshold = RegInit(0.U(64.W))
    // TODO: meip(0)(0) is read-only false.B
    val meip = RegInit(VecInit.fill(32){0.U(64.W)})
    // TODO: meie(0)(0) is read-only false.B
    val meie = RegInit(VecInit.fill(32){Fill(64, 1.U)}) // TODO: default: disable all
    dontTouch(meip)
    // TODO: End of the CSRs for a interrupt file

    // TODO: directly access TL protocol, instead of use the regmap
    val mseteipnum = RegInit(0.U(32.W))
    val mseteipnumRF = RegField(32, mseteipnum)
    mIntFileNode.regmap(
      0 -> Seq(mseteipnumRF)
    )
    // TODO: parameterization
    when (
      mseteipnum =/= 0.U
      & meie(mseteipnum(10,6))(mseteipnum(5,0))
    ) {
      // set meip bit
      meip(mseteipnum(10,6)) := meip(mseteipnum(10,6)) | (1.U << (mseteipnum(5,0)))
      mseteipnum := 0.U
    }

    val meipBools = Cat(meip.reverse).asBools
    val meieBools = Cat(meie.reverse).asBools
    toCSR.meip := ParallelOR(
      (meipBools zip meipBools).map {
        case (p: Bool, e: Bool) => p & e
    })
    toCSR.mtopei := Mux(
      toCSR.meip,
      ParallelPriorityMux(
        (meipBools zip meieBools).zipWithIndex.map {
          case ((p: Bool, e: Bool), i: Int) => (p & e, i.U)
      }),
      0.U
    )
  }
}

class TLIMSICWrapper()(implicit p: Parameters) extends LazyModule {
  val tl = TLClientNode(
    Seq(TLMasterPortParameters.v1(
      Seq(TLMasterParameters.v1("tl", IdRange(0, 16)))
  )))

  val imsic = LazyModule(new TLIMSIC(IntFileParams())(Parameters.empty))
  imsic.mIntFileNode := tl

  lazy val module = new LazyModuleImp(this) {
    tl.makeIOs()
  }
}

/**
 * Generate Verilog sources
 */
object TLIMSIC extends App {
  val top = DisableMonitors(p => LazyModule(
    new TLIMSICWrapper()(Parameters.empty))
  )(Parameters.empty)

  ChiselStage.emitSystemVerilog(
    top.module,
    // more opts see: $CHISEL_FIRTOOL_PATH/firtool -h
    firtoolOpts = Array(
      "-disable-all-randomization",
      "-strip-debug-info",
      // without this, firtool will exit with error: Unhandled annotation
      "--disable-annotation-unknown",
      "--lowering-options=explicitBitcast,disallowLocalVariables,disallowPortDeclSharing,locationInfoStyle=none",
      "--split-verilog", "-o=gen",
    )
  )
}
